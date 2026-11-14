"""The app. POC-03 serves the health check; commands, queues and the WebSocket follow (POC-04, POC-05)."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import SESSION
from .models import Job, JobEvent

app = FastAPI(title="OneFamilyServices ops", docs_url=None, redoc_url=None)


class Health(BaseModel):
    jobs: int
    events: int


@app.get("/api/health", response_model=Health)
async def health(session: AsyncSession = SESSION) -> Health:
    """A real read, so it fails when the database does."""
    jobs = await session.scalar(select(func.count()).select_from(Job))
    events = await session.scalar(select(func.count()).select_from(JobEvent))
    return Health(jobs=int(jobs or 0), events=int(events or 0))
