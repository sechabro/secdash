import logging
import os
import shutil
from collections import defaultdict
from datetime import datetime, tzinfo

from fastapi import HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

import schemas
from database import async_session_maker
from services import ipabuse_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def visitor_info_post(session: AsyncSession, item: schemas.Visitor):
    session.add(item)
    await session.commit()
    await session.refresh(item)
    logger.info(f' Visitor information documented successfully.')
    return item


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


async def get_visitors(session: AsyncSession) -> list[schemas.VisitorInMem]:
    result = await session.execute(select(schemas.Visitor))
    visitors = result.scalars().all()

    return [
        schemas.VisitorInMem(
            v.id, v.username, v.acct_created, v.ip, v.port, v.device_info,
            v.browser_info, v.is_bot, v.geo_info,
            v.ipdb.get("isTor", False),  # lean structure
            v.last_active, v.time_idle, v.is_active
        )
        for v in visitors
    ]


async def get_flagged_visitors(session: AsyncSession) -> list[schemas.VisitorsFlaggedSummary]:
    result = await session.execute(select(schemas.VisitorsFlagged))
    flagged_visitors = result.scalars().all()

    return [
        schemas.VisitorsFlaggedSummary(
            id=v.id,
            visitor_id=v.visitor_id,
            risk_level=v.risk_level,
            created_at=v.created_at
        )
        for v in flagged_visitors
    ]


async def get_flagged_visitor(session: AsyncSession, case_id: int) -> schemas.VisitorsFlagged:
    result = await session.execute(select(schemas.VisitorsFlagged).options(selectinload(schemas.VisitorsFlagged.visitor_info)).where(schemas.VisitorsFlagged.id == case_id))
    flagged_visitor = result.scalars().one_or_none()

    visitor = flagged_visitor.visitor_info

    return {
        "id": flagged_visitor.id,
        "visitor_id": flagged_visitor.visitor_id,
        "risk_level": flagged_visitor.risk_level,
        "justification": flagged_visitor.justification,
        "recommended_action": flagged_visitor.recommended_action,
        "created_at": flagged_visitor.created_at.isoformat(),
        "visitor_info": {
            "username": visitor.username,
            "acct_created": visitor.acct_created,
            "ip": visitor.ip,
            "port": visitor.port,
            "device_info": visitor.device_info,
            "browser_info": visitor.browser_info,
            "is_bot": visitor.is_bot,
            "geo_info": visitor.geo_info,
            "ipdb": visitor.ipdb,
            "last_active": visitor.last_active,
            "time_idle": visitor.time_idle,
            "is_active": visitor.is_active
        } if visitor else None
    }

# DRAGON [2025-05-19]: schemas.RiskLevel and schemas.ActionType functionality
# Default risk value for schemas.VisitorsFlagged.risk_level should be set to
# schemas.RiskLevel.flagged.


async def visitor_flag_post(session: AsyncSession, item: schemas.VisitorsFlagged) -> JSONResponse:
    session.add(item)
    await session.commit()
    await session.refresh(item)
    logger.info(
        f' Account {item.visitor_id} flagged successfully. Case created.')
    return JSONResponse(
        status_code=201,
        content={
            "message": f"Visitor {item.visitor_id} flagged successfully.",
            "case_id": item.id,
            "created_at": item.created_at.isoformat()
        }
    )


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


async def shutdown_db_update(session: AsyncSession, visitor_list: list) -> bool:
    try:
        for visitor in visitor_list:
            stmt = (
                update(schemas.Visitor)
                .where(schemas.Visitor.username == visitor.username)
                .values(
                    is_active=visitor.is_active,
                    last_active=visitor.last_active,
                    time_idle=visitor.time_idle
                )
            )
            await session.execute(stmt)

        await session.commit()
        return True
    except Exception:
        logger.exception("Failed to update database on shutdown.")
        return False
