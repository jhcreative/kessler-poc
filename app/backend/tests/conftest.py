"""Tests run against Postgres (TEST_DATABASE_URL), not SQLite: CHECKs, JSONB, identities and
transactions behave as they do in production. Each test runs inside a transaction that rolls back."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from ofs import models  # noqa: F401
from ofs.db import Base, get_session
from ofs.main import app

NOW = datetime(2026, 11, 16, 9, 0, tzinfo=UTC)  # demo morning, so seeded times are fixed


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(os.environ["TEST_DATABASE_URL"])
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        outer = await conn.begin()
        s = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield s
        finally:
            await s.close()
            await outer.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _session
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded(session: AsyncSession) -> AsyncSession:
    from ofs.seed import seed

    await seed(session, now=NOW)
    return session
