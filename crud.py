import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

from fastapi.concurrency import run_in_threadpool
from pydantic import EmailStr
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

import schemas
from database import async_session_maker
from ipset import ipset_calls
from services import ip_analysis_gathering, ipabuse_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# DRAGON [2025-05-24]: function refactor for only one commit
# Currently 1 or more commits per session, since it's inside
# the for-loop. Need to refactor appropriately so that commit
# only happens once: after all statement executions are done.
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


# DRAGON [2025-05-27]: refactor to call ip_status_update.
# Instead of performing its own `.where(...).values()` logic inline.
# Revisit post-MVP deploy.


async def ai_analysis_update(ip_updates: list[dict]):
    async with async_session_maker() as session:
        try:
            successful = 0
            for entry in ip_updates:
                status = None
                if entry["recommended_action"] == "autobanned":  # <--- autoban automation
                    await run_in_threadpool(ipset_calls, ip=entry["ip_address"], action="blacklist")
                    status = schemas.CurrentStatus.banned
                stmt = (
                    update(schemas.FailedLoginIntel)
                    .where(schemas.FailedLoginIntel.ip_address == entry.get("ip_address"))
                    .values(
                        analysis=entry["analysis"],
                        risk=schemas.RiskLevel(entry["risk_level"]),
                        action=schemas.ActionType(entry["recommended_action"]),
                        status_change_date=datetime.now(timezone.utc),
                        status=status if status else schemas.CurrentStatus.active
                    )
                )
                try:
                    await session.execute(stmt)
                    logger.info(
                        f' Analysis for {entry.get("ip_address")} completed. Update successful.'
                    )
                    successful += 1
                except Exception as e:
                    logger.error(
                        f' Failed to execute update for {entry.get("ip_address")} {e}')
            await session.commit()
            # return {"successful_updates": successful}
        except Exception as e:
            logger.error(f' Session Failure: {e}')


async def get_unanalyzed_ips() -> list[schemas.FailedLoginInMem]:
    try:
        logger.info(f' SSH monitoring started')
        while True:
            async with async_session_maker() as session:
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
                        count=result.count
                    )
                    for result in results
                    if result.ipdb is not None
                ]

                analyzed_ips = await ip_analysis_gathering(ip_info=for_analysis)
                await ai_analysis_update(ip_updates=analyzed_ips)
                await asyncio.sleep(60)

    except Exception as e:
        logger.error(f' 🤮 IP analysis loop crashed: {e}')


'''if __name__ == "__main__":
    bannit = asyncio.run(
        ai_analysis_update(
            ip_updates=[
                {
                    "recommended_action": "autobanned",
                    "risk_level": "black",
                    "analysis": "he's just a bad dude!",
                    "ip_address": "43.252.230.32"
                }
            ]
        )
    )
    print(bannit)'''
