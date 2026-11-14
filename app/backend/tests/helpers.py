from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ofs.commands import Actor
from ofs.models import Job, JobEvent, Person, Tech
from ofs.schemas import CommandIn
from ofs.states import ActorKind, Role

VALID: dict[str, dict[str, Any]] = {
    "record_client_approval": {"by": "Client facilities manager", "client_ref": "APR-1"},
    "assign_tech": {"tech": "Tech 1"},
    "reassign_tech": {"tech": "Tech 1"},
    "set_needs_review": {"reason": "Parts delay"},
    "close_job": {"actual_hours": 3.5, "sign_off_by": "Store manager"},
    "send_back_invoice": {"reason": "Wrong format"},
}


async def person(session: AsyncSession, label: str) -> Actor:
    p = (await session.execute(select(Person).where(Person.label == label))).scalar_one()
    return Actor(ActorKind.PERSON, p, Role(p.role))


async def tech_actor(session: AsyncSession, job: Job) -> Actor:
    tech = (await session.execute(select(Tech).where(Tech.id == job.tech_id))).scalar_one()
    p = (await session.execute(select(Person).where(Person.id == tech.person_id))).scalar_one()
    return Actor(ActorKind.PERSON, p, Role.TECH)


async def job_in(session: AsyncSession, state: str, **where: Any) -> Job:
    q = select(Job).where(Job.state == state).order_by(Job.number)
    for k, v in where.items():
        q = q.where(getattr(Job, k) == v)
    return (await session.execute(q.limit(1))).scalar_one()


def cmd(job: Job, command: str, payload: dict[str, Any] | None = None, override: str | None = None) -> CommandIn:
    return CommandIn(
        command=command,
        expected_event_id=job.last_event_id,
        payload=VALID.get(command, {}) if payload is None else payload,
        override_reason=override,
    )


async def event_count(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(JobEvent)) or 0)
