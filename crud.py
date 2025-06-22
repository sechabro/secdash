import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from fastapi.concurrency import run_in_threadpool
from pydantic import EmailStr
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

import schemas
from database import async_session_maker
from ipset import ipset_calls
from services import ip_analysis_gathering, ipabuse_check
from stream_manager import StreamManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
alerts = deque()
# alerts_queue = asyncio.Queue()


async def get_user_by_email(session: AsyncSession, email: EmailStr) -> schemas.UserInDb:
    statement = select(schemas.UserInDb).where(schemas.UserInDb.email == email)
    result = await session.execute(statement=statement)
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, user: schemas.UserReg) -> schemas.UserReg:
    regdate = str(datetime.now().isoformat())
    new_user = schemas.UserInDb(
        username=user.username, email=user.email, password=user.password, regdate=regdate)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.info(f' New user created successfully at {regdate}.')
    return user


async def get_all_ips(session: AsyncSession) -> list[schemas.FailedLoginInMem]:
    result = await session.execute(select(schemas.FailedLoginIntel))

    return [
        schemas.FailedLoginInMem(
            ip=row.ip_address,
            score=row.ipdb.get("abuseConfidenceScore", 0),
            is_tor=row.ipdb.get("isTor", False),
            total_reports=row.ipdb.get("totalReports", 0),
            country=row.ipdb.get("countryCode", "XX"),
            reco_action=row.action,
            count=row.count,
            risk=row.risk,
            status=row.status
        )
        for row in result.scalars().all()
        if row.ipdb is not None
    ]


async def upsert_failed_login_attempt(batch: list[list[str]]):
    ip_groups = defaultdict(list)

    for item in batch:
        ip_groups[item[1]].append(item)
    try:
        async with async_session_maker() as session:
            for ip, attempts in ip_groups.items():
                result = await session.execute(
                    select(schemas.FailedLoginIntel)
                    .where(schemas.FailedLoginIntel.ip_address == ip)
                )

                row_exists = result.scalar_one_or_none()
                new_attempts = [
                    {
                        "date": attempt[0],
                        "user": attempt[2],
                        "message": attempt[3]
                    }
                    for attempt in attempts
                ]
                if row_exists:
                    updated_attempts = row_exists.server_attempts + new_attempts

                    stmt = (
                        update(schemas.FailedLoginIntel)
                        .where(schemas.FailedLoginIntel.id == row_exists.id)
                        .values(
                            server_attempts=updated_attempts,
                            count=len(updated_attempts),
                            last_seen=datetime.fromisoformat(
                                updated_attempts[-1].get("date")).replace(tzinfo=None)
                        )
                    )
                    try:
                        await session.execute(stmt)
                        await session.commit()
                        logger.info(
                            f' New failed login attempt(s) from {ip} documented.'
                        )
                    except Exception as e:
                        logger.error(f' Commit Failure {e}')
                else:
                    first_seen_ts = datetime.fromisoformat(
                        new_attempts[0].get("date")).replace(tzinfo=None)
                    last_seen_ts = datetime.fromisoformat(
                        new_attempts[-1].get("date")).replace(tzinfo=None)
                    try:
                        ipdb_data = await ipabuse_check(ip)
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch AbuseIPDB data for {ip}: {e}")
                        ipdb_data = None
                    new_row = schemas.FailedLoginIntel(
                        ip_address=ip,
                        server_attempts=new_attempts,
                        count=len(new_attempts),
                        first_seen=first_seen_ts,
                        last_seen=last_seen_ts,
                        ipdb=ipdb_data
                    )
                    try:
                        session.add(new_row)
                        await session.commit()
                        logger.info(
                            f' New IP logged: {ip} — failed login attempt recorded.'
                        )
                    except Exception as e:
                        logger.error(f' Commit Failure: {e}')
    except Exception as e:
        logger.error(f' Session Failure: {e}')


# DRAGON [2025-05-27]: refactor to call ip_status_update.
# Instead of performing its own `.where(...).values()` logic inline.
# Revisit post-MVP deploy.


async def ip_status_update(ip: schemas.FailedLoginIPBan, session: AsyncSession):
    try:
        stmt = (
            update(schemas.FailedLoginIntel)
            .where(schemas.FailedLoginIntel.ip_address == ip.ip)
            .values(
                status=schemas.CurrentStatus[ip.status],
                status_change_date=datetime.now(timezone.utc)
            )
        )
        try:
            await session.execute(stmt)
            logger.info(
                f' Status update \"{ip.status}\" for {ip.ip} executed successfully.')
        except Exception as e:
            logger.error(
                f" Failed to execute status update for {ip.ip}: {e}"
            )
        await session.commit()
        return {"db_update": "successful"}
    except Exception as e:
        logger.error(f' Session Failure: {e}')


async def alert_queuing(alert: schemas.AlertInMem, alert_manager: StreamManager):
    await alert_manager.queue.put(alert)


async def insert_alert_from_mem(session: AsyncSession, alert: schemas.AlertInMem, alert_manager: Optional[StreamManager] = None):
    alert_db = schemas.AlertForDb(
        alert_type=alert.alert_type,
        ip_address=alert.ip,
        msg=alert.msg,
        date=alert.timestamp,
        status=schemas.AlertStatus.unread,
        ip_id=int(alert.ip_id)
    )
    session.add(alert_db)
    await session.flush()  # <-- to get access to the assigned id
    alert.alert_id = alert_db.id
    if alert_manager:
        try:
            await alert_queuing(alert=alert, alert_manager=alert_manager)
        except Exception as e:
            logger.info(f' Failed to queue alert {alert.alert_id}. {e}')


async def ai_analysis_update(ip_updates: list[dict], alert_manager: StreamManager):
    async with async_session_maker() as session:
        try:
            successful = 0
            for entry in ip_updates:
                async with session.begin_nested():
                    timestamp = datetime.now(timezone.utc)
                    alert = schemas.AlertInMem(
                        timestamp=timestamp,
                        ip=entry.get("ip_address"),
                        msg=f"Logged New IP {entry['ip_address']}!",
                        alert_type=schemas.AlertType.new_ip,
                        ip_id=entry.get("ip_id")
                    )
                    try:
                        status = None
                        if entry["recommended_action"] == "autoban":  # <--- autoban automation
                            await run_in_threadpool(ipset_calls, ip=entry["ip_address"], action="banned")
                            alert.alert_type = schemas.AlertType.autobanned
                            alert.msg = f"Autobanned New IP {alert.ip}!"
                            status = schemas.CurrentStatus.banned
                        stmt = (
                            update(schemas.FailedLoginIntel)
                            .where(schemas.FailedLoginIntel.ip_address == entry.get("ip_address"))
                            .values(
                                analysis=entry["analysis"],
                                risk=schemas.RiskLevel(entry["risk_level"]),
                                action=schemas.ActionType(
                                    entry["recommended_action"]),
                                status_change_date=timestamp,
                                status=status if status else schemas.CurrentStatus.active
                            )
                        )

                        await session.execute(stmt)
                        await insert_alert_from_mem(session=session, alert=alert, alert_manager=alert_manager)
                        logger.info(
                            f' {alert.msg} Analysis complete. Update successful.'
                        )
                        successful += 1
                    except Exception as e:
                        logger.error(
                            f' Failed to execute update for {entry.get("ip_address")} {e}')
                        # await session.rollback() <-- not needed with `session.begin_nested()`
            await session.commit()
            logger.info(f" {successful} successful updates.")

        except Exception as e:
            logger.error(f' Session Failure: {e}')


async def get_unanalyzed_ips(alert_manager: StreamManager) -> list[schemas.FailedLoginInMem]:
    try:
        logger.info(f' New IP monitoring started')
        while True:
            async with async_session_maker() as session:
                await asyncio.sleep(30)
                stmt = select(schemas.FailedLoginIntel).where(
                    (schemas.FailedLoginIntel.analysis == None) |
                    (schemas.FailedLoginIntel.risk == None) |
                    (schemas.FailedLoginIntel.action == schemas.ActionType.none)
                )
                results = (await session.execute(stmt)).scalars().all()

                for_analysis = [
                    schemas.FailedLoginInMem(
                        ip=result.ip_address,
                        score=result.ipdb.get("abuseConfidenceScore"),
                        is_tor=result.ipdb.get("isTor"),
                        total_reports=result.ipdb.get("totalReports"),
                        first_seen=result.first_seen.isoformat(),
                        last_seen=result.last_seen.isoformat(),
                        count=result.count,
                        ip_id=result.id
                    )
                    for result in results
                    if result.ipdb is not None
                ]

                if not for_analysis:
                    logger.info(f' Heartbeat. No new IP addresses detected.')
                    continue

                analyzed_ips = await ip_analysis_gathering(ip_info=for_analysis)
                await ai_analysis_update(ip_updates=analyzed_ips, alert_manager=alert_manager)

    except Exception as e:
        logger.error(f' 🤮 IP analysis loop crashed: {e}')


async def get_all_alerts(
        session: AsyncSession
) -> list[schemas.AlertInMem]:
    stmt = select(schemas.AlertForDb).order_by(
        schemas.AlertForDb.status.asc(),  # unread (0) comes before read (1)
        schemas.AlertForDb.date.desc()
    )
    results = (await session.execute(stmt)).scalars().all()
    return [
        asdict(schemas.AlertInMem(
            timestamp=result.date.isoformat(),
            alert_type=result.alert_type.value,
            msg=result.msg,
            ip=result.ip_address,
            alert_id=result.id,
            status=result.status
        )) for result in results
    ]


async def get_alert_and_ip(alert_id: int, session: AsyncSession) -> dict:
    result = await session.execute(
        select(schemas.AlertForDb)
        .options(joinedload(schemas.AlertForDb.intel))
        .where(schemas.AlertForDb.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    return {
        "alert_id": alert.id,
        "msg": alert.msg,
        "alert_type": alert.alert_type.value,
        "ip": alert.ip_address,
        "ip_id": alert.ip_id,
        "intel": {
            "status": alert.intel.status.value,
            "analysis": alert.intel.analysis,
            "risk_level": alert.intel.risk.value,
            "recommended_action": alert.intel.action.value,
            "country": alert.intel.ipdb.get("countryCode"),
            "score": alert.intel.ipdb.get("abuseConfidenceScore"),
            "attempt_count": alert.intel.count,
            "total_reports": alert.intel.ipdb.get("totalReports"),
            "first_seen": alert.intel.first_seen.isoformat(),
            "last_seen": alert.intel.last_seen.isoformat()

        } if alert.intel else None
    }


async def mark_alert_read(alert_id: int, session: AsyncSession):
    result = await session.execute(
        select(schemas.AlertForDb).where(schemas.AlertForDb.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if alert and alert.status != schemas.AlertStatus.read:
        alert.status = schemas.AlertStatus.read
        await session.commit()

'''if __name__ == "__main__":
    ip_updates = [
        {
            "ip_address": "192.168.1.20",
            "analysis": "Low risk",
            "risk_level": "green",
            "recommended_action": "monitor"
        },
        {
            "ip_address": "192.168.1.404",
            "analysis": "Invalid IP",
            "risk_level": "green",
            "recommended_action": "monito"  # <-- invalid enum value, will fail
        },
        {
            "ip_address": "192.168.1.21",
            "analysis": "High risk",
            "risk_level": "black",
            "recommended_action": "autoban"
        }
    ]
    asyncio.run(ai_analysis_update(ip_updates=ip_updates))
'''
