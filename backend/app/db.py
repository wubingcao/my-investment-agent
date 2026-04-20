from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_sessionmaker = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, future=True)
    return _engine


def get_sessionmaker():
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _sessionmaker


@asynccontextmanager
async def session_scope():
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    from app import models  # noqa: F401 — register models
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _auto_migrate(conn)


async def _auto_migrate(conn):
    """Add columns to existing tables when the ORM has new ones (SQLite)."""
    from sqlalchemy import text
    # List desired (table, column, ddl) tuples. Keep cheap and idempotent.
    migrations = [
        ("signal", "summary", "ALTER TABLE signal ADD COLUMN summary TEXT DEFAULT ''"),
    ]
    for table, col, ddl in migrations:
        res = await conn.exec_driver_sql(f"PRAGMA table_info({table})")
        cols = [row[1] for row in res.fetchall()]
        if col not in cols:
            await conn.exec_driver_sql(ddl)
