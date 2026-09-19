"""Database connection + SQLAlchemy session."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: provides a session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync():
    """Synchronous DB session for non-FastAPI contexts (e.g., WebSocket auth)."""
    return SessionLocal()


def init_db() -> None:
    """Creates tables (idempotent)."""
    from . import models  # noqa: F401  (registers models on Base.metadata)

    Base.metadata.create_all(bind=engine)
