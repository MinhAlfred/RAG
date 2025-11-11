"""Database connection and session management"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from config.settings import settings
from ..models.chat_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, database_url: str = None):
        if database_url:
            self.database_url = database_url
        elif settings.DATABASE_URL:
            self.database_url = settings.DATABASE_URL
        elif all([settings.user, settings.password, settings.host, settings.dbname]):
            self.database_url = (
                f"postgresql://{settings.user}:{settings.password}@"
                f"{settings.host}:{settings.port or '5432'}/{settings.dbname}"
            )
        else:
            raise ValueError("Missing DB config")

        # DÙNG asyncpg chuẩn, KHÔNG thêm query param lạ
        self.async_database_url = self.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

        self.async_engine = create_async_engine(
            self.async_database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )

        self.async_session_factory = async_sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info("✅ Database manager initialized (async mode)")

    async def create_tables(self):
        # DÙNG ORM TẠO BẢNG để khớp với Base/models
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self):
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        """Close database connections"""
        await self.async_engine.dispose()
        logger.info("✅ Database connections closed")


# Global database manager instance
_db_manager: DatabaseManager = None


def get_db_manager(force_new: bool = False) -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager

    if force_new and _db_manager is not None:
        _db_manager = None

    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session

    Usage in FastAPI endpoint:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            # Use db here
            pass
    """
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session
