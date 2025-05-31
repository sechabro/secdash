import logging
import os

from dotenv import load_dotenv
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import SQLModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

abpwd = os.getenv('ABPWD')
if abpwd is None:
    raise RuntimeError("ABPWD not found in environment variables")

DATABASE_URL = f"postgresql+asyncpg://aberdeen:{abpwd}@localhost:5432/secdash"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

############### IMPORTANT NOTICE REGARDING DATABASE ENGINE ##################
# This check is synchronous, and only runs at start-up, hence the "temp_sync"
# nomenclature. None of this is used in session activity. ###################
TEMP_SYNC_DB_URL = f"postgresql://aberdeen:{abpwd}@localhost:5432/secdash"
temp_sync_engine = create_engine(TEMP_SYNC_DB_URL, echo=False)


async def database_check() -> bool:
    def sync_db_check() -> bool:
        if not database_exists(temp_sync_engine.url):
            create_database(temp_sync_engine.url)
            logger.info(f' Database successfully created...\n')
            return True
        return False
    return await run_in_threadpool(sync_db_check)


async def create_tables() -> bool:
    def sync_create_tables() -> bool:
        with temp_sync_engine.begin() as conn:
            SQLModel.metadata.create_all(conn)
        return True
    return await run_in_threadpool(sync_create_tables)
############################################################################
############################################################################
############################################################################


async def get_session():
    async with async_session_maker() as session:
        yield session
