"""
Database configuration and SQLAlchemy setup for Solmar Workflow Automation Platform.
Supports both SQLite (development) and PostgreSQL (production) with async support.
"""
import os
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    AsyncConnection,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase, declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from ..config import settings

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Provides consistent timestamp columns and serialization methods.
    """
    pass


class Database:
    """Database connection manager with async SQLAlchemy setup."""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        
    def get_engine(self) -> AsyncEngine:
        """Get or create the async database engine."""
        if self._engine is None:
            # Determine database URL from environment
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite configuration
                self._engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DEBUG,
                    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
                )
            else:
                # PostgreSQL configuration with connection pooling
                self._engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DEBUG,
                    poolclass=QueuePool,
                    pool_size=settings.DATABASE_POOL_SIZE,
                    max_overflow=settings.DATABASE_MAX_OVERFLOW,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # Recycle connections every hour
                )
        
        return self._engine
    
    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the async session factory."""
        if self._session_factory is None:
            engine = self.get_engine()
            self._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        
        return self._session_factory
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session as an async context manager."""
        session_factory = self.get_session_factory()
        
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.get_engine().connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def create_tables(self):
        """Create all tables from SQLAlchemy models (for development/testing)."""
        async with self.get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all tables (for testing purposes)."""
        async with self.get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Global database instance
database = Database()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to inject database session into FastAPI endpoints.
    
    Example usage:
    ```python
    from .db.database import get_db_session
    
    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db_session)):
        result = await db.execute(select(User))
        return result.scalars().all()
    ```
    """
    async for session in database.get_session():
        yield session


async def init_db():
    """Initialize database tables (call during application startup)."""
    await database.create_tables()


async def check_db_health() -> dict:
    """Health check for database connectivity."""
    is_healthy = await database.health_check()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
        "connected": is_healthy
    }