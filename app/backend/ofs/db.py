"""The database: one async engine, one session per request, closed before the response.

From Tailor's practice (ADR-0102): a request's session commits, or rolls back, and closes when the
endpoint returns, ahead of the response and any background task. So a failed commit is never
reported as a 200.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set (see app/.env.example)")
    return url


engine = create_async_engine(database_url(), pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


SESSION = Depends(get_session, scope="function")


@asynccontextmanager
async def open_session() -> AsyncIterator[AsyncSession]:
    """A short session outside a request: the WebSocket takes one per read, never one for the whole connection,
    so a hundred open views don't hold a hundred pooled connections."""
    async with SessionFactory() as session:
        yield session
