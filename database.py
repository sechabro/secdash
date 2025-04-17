import os
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

abpwd = str(os.getenv('ABPWD', default=None))

DATABASE_URL = f"postgresql+asyncpg://aberdeen:{abpwd}@localhost:5432/secdash"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

############### IMPORTANT NOTICE REGARDING DATABASE ENGINE ##################
# This check is synchronous, and only runs at start-up, hence the "temp_sync"
# nomenclature. None of this is used in session activity. ###################
TEMP_SYNC_DB_URL = f"postgresql://aberdeen:{abpwd}@localhost:5432/secdash"
temp_sync_engine = create_engine(TEMP_SYNC_DB_URL, echo=True)


def database_check():
    if not database_exists(temp_sync_engine.url):
        create_database(temp_sync_engine.url)
        logger.info(f' Database successfully created...')
        return True
    logger.info(f' Database already exists...')
    return False
############################################################################
############################################################################
############################################################################


async def get_session():
    async with async_session_maker() as session:
        yield session
