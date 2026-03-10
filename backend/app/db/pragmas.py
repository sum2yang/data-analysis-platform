from sqlalchemy import event
from sqlalchemy.engine import Engine

__all__ = ["register_sqlite_pragmas"]


def register_sqlite_pragmas() -> None:
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
