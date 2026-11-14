"""The job API. Reads are scoped by role: a tech sees only their own queue (T1). Writes go through commands only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from sqlalchemy import Select, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas
from .auth import CURRENT, Caller, check_origin
from .commands import Actor, envelope, execute, job_out
from .db import SESSION
from .hub import Message, hub
from .models import Job, JobEvent, Tech
from .states import QUEUE, ActorKind, Role, State

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


async def _scoped(session: AsyncSession, caller: Caller) -> Select[Job]:
    q = select(Job)
    if caller.role is Role.TECH:
        tech = await session.scalar(select(Tech).where(Tech.person_id == caller.person.id))
        q = q.where(Job.tech_id == (tech.id if tech else None))
    return q


@router.get("", response_model=list[schemas.JobOut])
async def list_jobs(
    caller: Caller = CURRENT,
    session: AsyncSession = SESSION,
    state: State | None = None,
    queue: str | None = None,
    mine: bool = Query(False, description="The coordinator's own jobs (C1)"),
) -> list[schemas.JobOut]:
    q = await _scoped(session, caller)
    if state:
        q = q.where(Job.state == state.value)
    if queue:
        q = q.where(Job.state.in_([s.value for s, name in QUEUE.items() if name == queue]))
    if mine:
        q = q.where(Job.owner_id == caller.person.id)
    jobs = (await session.execute(q.order_by(Job.number))).scalars().all()
    return [await job_out(session, j) for j in jobs]


async def _one(session: AsyncSession, caller: Caller, job_id: uuid.UUID) -> Job:
    job = await session.scalar((await _scoped(session, caller)).where(Job.id == job_id))
    if job is None:
        raise HTTPException(404, "There's no such job in your view")
    return job


@router.get("/{job_id}", response_model=schemas.JobOut)
async def get_job(job_id: uuid.UUID, caller: Caller = CURRENT, session: AsyncSession = SESSION) -> schemas.JobOut:
    return await job_out(session, await _one(session, caller, job_id))


@router.get("/{job_id}/events", response_model=list[schemas.EventEnvelope])
async def job_events(
    job_id: uuid.UUID, caller: Caller = CURRENT, session: AsyncSession = SESSION
) -> list[schemas.EventEnvelope]:
    job = await _one(session, caller, job_id)
    events = (await session.execute(select(JobEvent).where(JobEvent.job_id == job.id).order_by(JobEvent.id))).scalars()
    return [envelope(e, job.number) for e in events]


_REFUSALS: dict[int | str, dict[str, Any]] = {
    code: {"model": schemas.Refusal, "description": why}
    for code, why in (
        (403, "Your role can't do this"),
        (404, "Not a job you can see"),
        (409, "Stale, or the wrong state"),
        (422, "The payload or a rail"),
    )
}


@router.post("/{job_id}/commands", response_model=schemas.CommandResult, responses=_REFUSALS)
async def run_command(
    job_id: uuid.UUID,
    cmd: schemas.CommandIn,
    request: Request,
    background: BackgroundTasks,
    caller: Caller = CURRENT,
    session: AsyncSession = SESSION,
) -> schemas.CommandResult:
    check_origin(request)
    if caller.role is Role.EXEC:
        raise HTTPException(403, "The overview is read-only")
    before = await session.scalar(select(Job.tech_id).where(Job.id == job_id))
    job, events = await execute(session, job_id, cmd, Actor(ActorKind.PERSON, caller.person, caller.role))
    result = schemas.CommandResult(job=await job_out(session, job), events=[envelope(e, job.number) for e in events])
    # Runs after the session commits (function scope, ADR-0102): only committed changes are ever published.
    background.add_task(hub.publish, messages(result, before))
    return result


def messages(result: schemas.CommandResult, tech_before: uuid.UUID | None) -> list[Message]:
    techs = frozenset(t for t in (tech_before, result.job.tech_id) if t)
    return [Message(schemas.LiveEvent(event=e, job=result.job).model_dump(mode="json"), techs) for e in result.events]


overview_router = APIRouter(prefix="/api/overview", tags=["overview"])

# Time in each state: from a state-changing event to the next one on the same job (field edits don't count).
_TURNAROUND = text("""
    WITH moves AS (
        SELECT job_id, to_state, at,
               lead(at) OVER (PARTITION BY job_id ORDER BY id) AS left_at
        FROM job_events
        WHERE from_state IS DISTINCT FROM to_state
    )
    SELECT to_state,
           count(*) FILTER (WHERE left_at IS NULL) AS open,
           avg(extract(epoch FROM (:now - at)) / 3600) FILTER (WHERE left_at IS NULL) AS open_hours_avg,
           count(*) FILTER (WHERE left_at IS NOT NULL) AS done,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM (left_at - at)) / 3600)
               FILTER (WHERE left_at IS NOT NULL) AS done_hours_median
    FROM moves
    GROUP BY to_state
""")


@overview_router.get("", response_model=schemas.Overview)
async def overview(caller: Caller = CURRENT, session: AsyncSession = SESSION) -> schemas.Overview:
    """G3 and Q9: every job by state and queue, and how long each step takes. Office roles and exec only."""
    if caller.role is Role.TECH:
        raise HTTPException(403, "The overview is for the office")
    now = datetime.now(UTC)
    rows = {r.to_state: r for r in (await session.execute(_TURNAROUND, {"now": now})).all()}

    def hours(v: object) -> float | None:
        return None if v is None else round(float(v), 1)  # type: ignore[arg-type]

    steps = []
    for state in State:
        r = rows.get(state.value)
        steps.append(
            schemas.StepTurnaround(
                state=state,
                queue=QUEUE[state],
                open=int(r.open) if r else 0,
                open_hours_avg=hours(r.open_hours_avg) if r else None,
                done=int(r.done) if r else 0,
                done_hours_median=hours(r.done_hours_median) if r else None,
            )
        )
    return schemas.Overview(total=sum(s.open for s in steps), steps=steps, as_of=now)
