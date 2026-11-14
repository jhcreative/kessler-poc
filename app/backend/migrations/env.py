"""Alembic, async, against DATABASE_URL. The models are the source; each migration is reviewed."""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.engine import Connection

from ofs import models  # noqa: F401  (registers the tables)
from ofs.db import Base, engine

target_metadata = Base.metadata


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def _main() -> None:
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


asyncio.run(_main())
