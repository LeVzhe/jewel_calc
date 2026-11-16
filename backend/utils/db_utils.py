import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.settings import settings

logger = logging.getLogger(__name__)


class DbManager:
    engine = create_async_engine(
        settings.database_url_asyncpg,
        echo=False,
        pool_pre_ping=True,
        connect_args={"timeout": 10},
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    @classmethod
    async def connect(cls) -> None:
        async with cls.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("Database connection established")

    @classmethod
    async def dispose(cls) -> None:
        await cls.engine.dispose()
