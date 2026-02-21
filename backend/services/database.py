import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./neurotutor.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class DatabaseService:
    """Database service for CRUD operations."""

    @staticmethod
    async def get_session() -> AsyncSession:
        async with async_session_maker() as session:
            return session

    @staticmethod
    async def commit(session: AsyncSession) -> None:
        await session.commit()

    @staticmethod
    async def rollback(session: AsyncSession) -> None:
        await session.rollback()

    @staticmethod
    async def refresh(session: AsyncSession, instance: object) -> None:
        await session.refresh(instance)
