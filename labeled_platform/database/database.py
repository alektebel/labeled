"""Database connection and management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from .models import Base


class Database:
    """Database manager."""

    def __init__(self, database_url: str = None):
        """
        Initialize database.

        Args:
            database_url: SQLAlchemy database URL
        """
        if database_url is None:
            # Default to SQLite for development
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite:///./labeled_platform.db"
            )

        # Handle PostgreSQL URL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            echo=False
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# Global database instance
_db_instance = None


def init_db(database_url: str = None) -> Database:
    """Initialize global database instance."""
    global _db_instance
    _db_instance = Database(database_url)
    _db_instance.create_tables()
    return _db_instance


def get_db() -> Generator[Session, None, None]:
    """Get database session (FastAPI dependency)."""
    if _db_instance is None:
        init_db()
    return _db_instance.get_session()
