"""
Database configuration and connection management.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from databases import Database

from utils.config import get_config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.config = get_config()
        self._engine = None
        self._database = None
        self._session_factory = None
        self._initialized = False
    
    @property
    def database_url(self) -> str:
        """Get the database URL from configuration."""
        if self.config.database.url:
            return self.config.database.url
        
        # Build URL from individual components
        username = self.config.database.username or "postgres"
        password = self.config.database.password or ""
        host = self.config.database.host
        port = self.config.database.port
        database = self.config.database.name
        
        if password:
            return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
        else:
            return f"postgresql+asyncpg://{username}@{host}:{port}/{database}"
    
    async def initialize(self):
        """Initialize database connections."""
        if self._initialized:
            return
        
        try:
            # Create async engine
            self._engine = create_async_engine(
                self.database_url,
                echo=self.config.debug,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create databases instance for raw queries
            database_url_sync = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
            self._database = Database(database_url_sync)
            
            await self._database.connect()
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        if self._database:
            await self._database.disconnect()
        
        if self._engine:
            await self._engine.dispose()
        
        self._initialized = False
        logger.info("Database connections closed")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if not self._initialized:
            await self.initialize()
        
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @property
    def database(self) -> Database:
        """Get the raw database connection."""
        if not self._database:
            raise RuntimeError("Database not initialized")
        return self._database
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        if not self._initialized:
            return False
        
        try:
            result = await self._database.fetch_one("SELECT 1 as health")
            return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions in FastAPI."""
    async for session in db_manager.get_session():
        yield session


async def init_db():
    """Initialize database on application startup."""
    await db_manager.initialize()


async def close_db():
    """Close database on application shutdown."""
    await db_manager.close()