"""PostgreSQL client using SQLAlchemy."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings


class PostgresClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PostgresClient, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'engine'):
            self.engine = create_engine(
                settings.database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine)
            self.Base = declarative_base()

    def init_db(self):
        self.Base.metadata.create_all(bind=self.engine)

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


postgres_client = PostgresClient()
