"""PostgreSQL client using SQLAlchemy."""

from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings
from database import Base

class PostgresClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PostgresClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        print(f"Connection client: {settings.database_url}")

        if not hasattr(self, 'engine'):
            self.engine = create_engine(settings.database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
            self.async_engine = create_async_engine(async_url, pool_pre_ping=True)
            self.AsyncSessionLocal = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False
            )

    def init_db(self):
        Base.metadata.create_all(bind=self.engine)

    def get_db(self):
        """Get database engine."""
        return self.engine

    @contextmanager
    def get_session(self):
        """Get database session with context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_instance(self) -> Session:
        """Get a new session instance."""
        return self.SessionLocal()

    @asynccontextmanager
    async def get_async_session(self):
        """Get async database session with context manager."""
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def get_async_session_instance(self) -> AsyncSession:
        """Get a new async session instance."""
        return self.AsyncSessionLocal()

postgres_client = PostgresClient()
