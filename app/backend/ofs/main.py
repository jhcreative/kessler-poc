"""The app: auth, the job API and its commands, the live socket, the health check."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import api, auth, ws
from .commands import Refused
from .db import SESSION
from .models import Job, JobEvent
from .schemas import Refusal

# No docs and no served schema: the OpenAPI is exported offline for the TypeScript types (scripts/types.sh).
app = FastAPI(title="OneFamilyServices ops", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(auth.router)
app.include_router(api.router)
app.include_router(api.overview_router)
app.include_router(ws.router)


@app.exception_handler(Refused)
async def refused(_request: Request, exc: Refused) -> JSONResponse:
    """A refused command: nothing was written (the session rolled back), and the reason says what to do."""
    body = Refusal(code=exc.code, reason=exc.reason)  # type: ignore[arg-type]
    return JSONResponse(status_code=exc.status, content=body.model_dump())


class Health(BaseModel):
    jobs: int
    events: int


@app.get("/api/health", response_model=Health)
async def health(session: AsyncSession = SESSION) -> Health:
    """A real read, so it fails when the database does."""
    jobs = await session.scalar(select(func.count()).select_from(Job))
    events = await session.scalar(select(func.count()).select_from(JobEvent))
    return Health(jobs=int(jobs or 0), events=int(events or 0))
