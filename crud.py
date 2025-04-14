from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from pydantic import EmailStr
import schemas
from fastapi import UploadFile, HTTPException, status, Request
import shutil
import os
import logging
from datetime import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# import aiofiles


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


async def register_user(session: AsyncSession, user: schemas.UserReg):
    regdate = str(datetime.now().isoformat())
    new_user = schemas.UserInDb(
        username=user.username, email=user.email, password=user.password, regdate=regdate)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.info(f' New user created successfully at {regdate}.')
    return schemas.User(username=user.username)
