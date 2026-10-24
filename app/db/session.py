"""Database engine + session factory (Phase 3).

DATABASE_URL decides the backend: SQLite for local/dev (default),
PostgreSQL in production (postgresql+psycopg://...). Tables are created
via Base.metadata.create_all for dev convenience; Alembic migrations
(migrations/) are the production path.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

Base = declarative_base()


def make_engine(database_url: str):
    if database_url in ("sqlite://", "sqlite:///:memory:"):
        return create_engine(database_url, connect_args={"check_same_thread": False},
                             poolclass=StaticPool)
    if database_url.startswith("sqlite:///"):
        path = database_url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(database_url, pool_pre_ping=True)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app.models import tables  # noqa: F401  (register models)
    Base.metadata.create_all(bind=engine)
