"""SQLAlchemy sessions; durable PostgreSQL in production, SQLite for local tests."""

import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool


class Base(DeclarativeBase):
    pass


@lru_cache
def engine_for(url: str):
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options.update(connect_args={"check_same_thread": False})
        if ":memory:" in url:
            options["poolclass"] = StaticPool
    else:
        options["poolclass"] = NullPool
    return create_engine(url, **options)


def configured_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured. Browser demo remains available.")
    if (os.getenv("VERCEL") or os.getenv("APP_ENV") == "production") and not url.startswith(
        ("postgres://", "postgresql://", "postgresql+psycopg://")
    ):
        raise RuntimeError("Production requires PostgreSQL; SQLite is only for local development.")
    return url


def get_db():
    from fastapi import HTTPException

    try:
        engine = engine_for(configured_url())
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
