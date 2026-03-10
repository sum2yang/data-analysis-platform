from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.pragmas import register_sqlite_pragmas

__all__ = ["engine", "SessionLocal", "get_db"]

_settings = get_settings()

engine = create_engine(
    _settings.sqlite_url,
    echo=_settings.DB_ECHO,
    connect_args={"check_same_thread": False},
)

register_sqlite_pragmas()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
