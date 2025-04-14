import os
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

abpwd = str(os.getenv('ABPWD', default=None))
DATABASE_URL = f"postgresql+asyncpg://aberdeen:{abpwd}@localhost:5432/secdash"


engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def database_check():
    if not database_exists(engine.url):
        create_database(engine.url)
        logger.info(f' Database successfully created...')
        return True
    logger.info(f' Database already exists...')
    return False


async def get_session():
    async with async_session_maker() as session:
        yield session
