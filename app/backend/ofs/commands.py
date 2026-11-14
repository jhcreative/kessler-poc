"""Commands: the only way a job moves (plan §4).

A view sends a command; this module checks it, in order:

1. the command exists (`states.TRANSITIONS`, or `update_fields`);
2. the caller's role may issue it, and a tech acts only on their own job;
3. the view saw the job's latest version (`expected_event_id`), so two people can't both move it from one state;
4. the job is in a state the command starts from;
5. the payload matches the command's model (`schemas.REQUESTS`);
6. the rails.

Then it writes the job and one `job_events` row, in the caller's transaction. Publishing the events after the commit
is POC-05's.

The rails (plan §4). Three are hard: nobody overrides them.
- A job that needs the client's approval can't be dispatched until the approval is on record.
- A job can't close without a sign-off or a reason.
- An invoice that failed its check can't be approved.

Anything else can be overridden by a person who gives a reason, and the reason is recorded on the event. Today that's
assigning a tech without the skill or the license for the site's state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas
from .models import Client, Contract, FleetPosition, Invoice, Job, JobEvent, Person, QbLedger, Site, Tech
from .rules import evaluate
from .states import FIELD_EDITORS, FINAL, QUEUE, TRANSITIONS, UPDATE_FIELDS, ActorKind, Role, State


class Refused(Exception):
    """A command the backend won't run. `reason` is a sentence the person can act on."""

    def __init__(self, status: int, code: str, reason: str) -> None:
        super().__init__(reason)
        self.status, self.code, self.reason = status, code, reason


@dataclass(frozen=True)
class Actor:
    kind: ActorKind
    person: Person | None = None
    role: Role | None = None

    @property
    def label(self) -> str:
        if self.person:
            return self.person.label
        return "Simulator" if self.kind is ActorKind.SIMULATOR else "System"


SYSTEM = Actor(ActorKind.SYSTEM)


def _words(command: str) -> str:
    return command.replace("_", " ")


async def _tech_of(session: AsyncSession, person: Person) -> Tech | None:
    return await session.scalar(select(Tech).where(Tech.person_id == person.id))


async def _record(
    session: AsyncSession,
    job: Job,
    command: str,
    source: State,
    target: State,
    actor: Actor,
    payload: dict[str, Any],
    override_reason: str | None,
    now: datetime,
) -> JobEvent:
    event = JobEvent(
        job_id=job.id,
        at=now,
        actor_kind=actor.kind.value,
        actor_id=actor.person.id if actor.person else None,
        actor_label=actor.label,
        command=command,
        from_state=source.value,
        to_state=target.value,
        payload=payload,
        override_reason=override_reason,
    )
    session.add(event)
    await session.flush()
    job.state = target.value
    job.last_event_id = event.id
    job.updated_at = now
    return event


async def execute(
    session: AsyncSession,
    job_id: uuid.UUID,
    cmd: schemas.CommandIn,
    actor: Actor,
    now: datetime | None = None,
) -> tuple[Job, list[JobEvent]]:
    """Run one command for a person (or the simulator). Raises `Refused`; writes nothing if it does."""
    now = now or datetime.now(UTC)
    job = await session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise Refused(404, "not_allowed", "There's no such job")
    if actor.role is Role.TECH:
        tech = await _tech_of(session, actor.person) if actor.person else None
        if tech is None or job.tech_id != tech.id:
            raise Refused(404, "not_allowed", "There's no such job in your queue")

    if cmd.command == UPDATE_FIELDS:
        return job, [await _update_fields(session, job, cmd, actor, now)]

    t = TRANSITIONS.get(cmd.command)
    if t is None:
        raise Refused(422, "not_allowed", f"There's no command called {cmd.command!r}")
    if actor.kind is ActorKind.PERSON and actor.role not in t.roles:
        raise Refused(403, "role", f"{actor.label} can't {_words(cmd.command)}")
    if cmd.expected_event_id != job.last_event_id:
        raise Refused(409, "stale", "This job changed since you opened it. Look at the new version, then try again")
    source = State(job.state)
    if source not in t.sources:
        raise Refused(409, "not_allowed", f"You can't {_words(cmd.command)} while the job is {_words(source)}")
    req = _validate(cmd.command, cmd.payload)

    payload, override = await HANDLERS[cmd.command](session, job, req, actor, cmd.override_reason, now)
    events = [await _record(session, job, cmd.command, source, t.target, actor, payload, override, now)]
    if cmd.command == "close_job":  # the invoice is drafted at close (plan §5)
        events.append(await run_system(session, job, "draft_invoice", now))
    return job, events


async def run_system(session: AsyncSession, job: Job, command: str, now: datetime | None = None) -> JobEvent:
    """A step the backend takes itself: the invoice at close, a payment from QuickBooks (simulated)."""
    now = now or datetime.now(UTC)
    t = TRANSITIONS[command]
    source = State(job.state)
    if source not in t.sources:
        raise Refused(409, "not_allowed", f"The system can't {_words(command)} while the job is {_words(source)}")
    payload, _ = await HANDLERS[command](session, job, schemas.NoPayload(), SYSTEM, None, now)
    return await _record(session, job, command, source, t.target, SYSTEM, payload, None, now)


def _validate(command: str, payload: dict[str, Any]) -> BaseModel:
    try:
        return schemas.REQUESTS[command].model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"]) or "payload"
        raise Refused(422, "not_allowed", f"{_words(command).capitalize()}: {where}: {first['msg']}") from exc


# --- one handler per command: (session, job, request, actor, override_reason, now) -> (event payload, override) ---

Result = tuple[dict[str, Any], str | None]


async def _contract(session: AsyncSession, job: Job) -> Contract:
    return (await session.execute(select(Contract).where(Contract.client_id == job.client_id))).scalar_one()


async def _none(session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime) -> Result:
    return {}, None


async def _qualify(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    if actor.person:
        job.owner_id = actor.person.id
    return {}, None


async def _record_approval(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    assert isinstance(req, schemas.ClientApprovalPayload)
    job.approval = {"by": req.by, "at": now.isoformat(), "client_ref": req.client_ref}
    return req.model_dump(mode="json"), None


async def _approve_for_dispatch(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    if job.requires_approval and job.approval is None:
        raise Refused(422, "rail", f"{job.rule_fired}. Record the client's approval before dispatch")
    return {}, None


async def _assign(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    assert isinstance(req, schemas.AssignPayload)
    row = (
        await session.execute(select(Tech).join(Person, Person.id == Tech.person_id).where(Person.label == req.tech))
    ).scalar_one_or_none()
    if row is None:
        raise Refused(422, "not_allowed", f"There's no tech called {req.tech!r}")
    site = (await session.execute(select(Site).where(Site.id == job.site_id))).scalar_one()
    gaps = [f"isn't licensed in {site.state}"] if site.state not in row.licenses else []
    if job.issue_type not in row.skills:
        gaps.append(f"has no {job.issue_type} skill")
    override = None
    if gaps:
        if not o:
            raise Refused(422, "rail", f"{req.tech} {' and '.join(gaps)}. Give a reason to assign anyway")
        override = o
    job.tech_id = row.id
    start = req.window_start or now + timedelta(hours=1)
    job.window_start, job.window_end = start, start + timedelta(hours=2)
    return {"tech": req.tech, "window_start": start.isoformat()}, override


async def _arrive(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    await _move_truck(session, job, "onsite", now)
    return {}, None


async def _needs_review(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    assert isinstance(req, schemas.ReasonPayload)
    job.extenuating_note = req.reason
    return req.model_dump(mode="json"), None


async def _return_to_dispatch(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    await _move_truck(session, job, "parked", now)
    job.tech_id, job.window_start, job.window_end = None, None, None
    return {}, None


async def _close(session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime) -> Result:
    assert isinstance(req, schemas.ClosePayload)
    if not req.sign_off_by and not req.no_sign_off_reason:
        raise Refused(422, "rail", "A job can't close without the site's sign-off, or a reason there isn't one")
    job.actual_hours = req.actual_hours
    job.sign_off = {"by": req.sign_off_by, "at": now.isoformat()} if req.sign_off_by else None
    if req.no_sign_off_reason:
        job.extenuating_note = req.no_sign_off_reason
    job.final_cents = job.final_cents if job.final_cents is not None else job.estimate_cents
    await _move_truck(session, job, "parked", now)
    return req.model_dump(mode="json", exclude_none=True), None


def invoice_check(job: Job) -> str | None:
    """Why the drafted invoice would be disputed, or None if it passes."""
    problems = []
    if job.sign_off is None:
        problems.append("no sign-off from the site")
    if job.requires_approval and job.approval is None:
        problems.append("the client's approval isn't on record")
    if job.final_cents is not None and job.final_cents > job.estimate_cents * 1.1:
        problems.append("the final is more than 10% over the estimate")
    return "; ".join(problems).capitalize() or None


async def _draft_invoice(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    client = (await session.execute(select(Client).where(Client.id == job.client_id))).scalar_one()
    total = job.final_cents if job.final_cents is not None else job.estimate_cents
    labor = round(total * 0.6 / 100) * 100  # synthetic split: the demo's invoices aren't priced from a rate card
    lines = [
        {"desc": f"Labor, {job.actual_hours or 0} h", "cents": labor},
        {"desc": "Parts and materials", "cents": total - labor},
    ]
    note = invoice_check(job)
    invoice = await session.scalar(select(Invoice).where(Invoice.job_id == job.id))
    if invoice is None:
        invoice = Invoice(job_id=job.id, created_at=now, qb_doc_number=None)
        session.add(invoice)
    invoice.lines, invoice.total_cents, invoice.format = lines, total, client.invoice_format
    invoice.state, invoice.check_passed, invoice.check_note = "draft", note is None, note
    await session.flush()
    return {}, None


async def _invoice(session: AsyncSession, job: Job) -> Invoice:
    invoice = await session.scalar(select(Invoice).where(Invoice.job_id == job.id))
    if invoice is None:
        raise Refused(409, "not_allowed", "This job has no drafted invoice")
    return invoice


async def _approve_invoice(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    invoice = await _invoice(session, job)
    if not invoice.check_passed:
        raise Refused(422, "rail", f"The invoice failed its check: {invoice.check_note}. Send it back")
    last = await session.scalar(select(func.max(QbLedger.doc_number)))
    doc = f"QB-{int(last[3:]) + 1 if last else 20450}"
    contract = await _contract(session, job)
    invoice.state, invoice.qb_doc_number = "submitted", doc
    session.add(
        QbLedger(
            invoice_id=invoice.id,
            client_id=job.client_id,
            doc_number=doc,
            amount_cents=invoice.total_cents,
            issued_at=now,
            due_at=now + timedelta(days=contract.net_days),
            paid_at=None,
        )
    )
    return {"qb_doc_number": doc}, None


async def _send_back(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    assert isinstance(req, schemas.ReasonPayload)
    invoice = await _invoice(session, job)
    invoice.state = "sent_back"
    return req.model_dump(mode="json"), None


async def _record_payment(
    session: AsyncSession, job: Job, req: BaseModel, actor: Actor, o: str | None, now: datetime
) -> Result:
    invoice = await _invoice(session, job)
    entry = (await session.execute(select(QbLedger).where(QbLedger.invoice_id == invoice.id))).scalar_one()
    entry.paid_at = now
    return {"qb_doc_number": entry.doc_number}, None


async def _move_truck(session: AsyncSession, job: Job, status: str, now: datetime) -> None:
    """Simulated Samsara: the truck sits at the site while the tech works there."""
    if job.tech_id is None:
        return
    tech = (await session.execute(select(Tech).where(Tech.id == job.tech_id))).scalar_one()
    pos = await session.get(FleetPosition, tech.truck)
    if pos is None:
        return
    if status == "onsite":
        site = (await session.execute(select(Site).where(Site.id == job.site_id))).scalar_one()
        pos.lat, pos.lng = site.lat, site.lng
    pos.status, pos.at = status, now


HANDLERS: dict[str, Any] = {
    "draft_intake": _none,
    "qualify": _qualify,
    "request_client_approval": _none,
    "record_client_approval": _record_approval,
    "approve_for_dispatch": _approve_for_dispatch,
    "assign_tech": _assign,
    "arrive": _arrive,
    "set_needs_review": _needs_review,
    "reassign_tech": _assign,
    "return_to_dispatch": _return_to_dispatch,
    "ask_to_wait": _none,
    "close_job": _close,
    "draft_invoice": _draft_invoice,
    "approve_invoice": _approve_invoice,
    "send_back_invoice": _send_back,
    "record_payment": _record_payment,
}


async def _update_fields(
    session: AsyncSession, job: Job, cmd: schemas.CommandIn, actor: Actor, now: datetime
) -> JobEvent:
    """Part B, two-way: the coordinator and the job's tech edit the same typed fields (plan §5)."""
    if actor.role not in FIELD_EDITORS:
        raise Refused(403, "role", f"{actor.label} can't edit the job's fields")
    if cmd.expected_event_id != job.last_event_id:
        raise Refused(409, "stale", "This job changed since you opened it. Look at the new version, then try again")
    state = State(job.state)
    if state in FINAL:
        raise Refused(409, "not_allowed", f"The job is {_words(state)}; its fields are final")
    req = _validate(UPDATE_FIELDS, cmd.payload)
    assert isinstance(req, schemas.FieldsIn)
    changes = req.model_dump(exclude_unset=True)
    if not changes:
        raise Refused(422, "not_allowed", "Nothing to change")
    if "estimate_cents" in changes and actor.role is not Role.COORDINATOR:
        raise Refused(403, "role", "Only the coordinator changes the estimate")
    if "issue_type" in changes:
        contract = await _contract(session, job)
        if changes["issue_type"] not in contract.issue_types:
            raise Refused(422, "not_allowed", f"{changes['issue_type']!r} isn't an issue type in this contract")
    for key, value in changes.items():
        setattr(job, key, value)
    if {"issue_type", "estimate_cents"} & changes.keys():
        contract = await _contract(session, job)
        job.requires_approval, job.rule_fired = evaluate(contract.rules, job.issue_type, job.estimate_cents)
    payload = {"changes": schemas.FieldsIn(**changes).model_dump(mode="json", exclude_unset=True)}
    return await _record(session, job, UPDATE_FIELDS, state, state, actor, payload, cmd.override_reason, now)


async def job_out(session: AsyncSession, job: Job) -> schemas.JobOut:
    client = (await session.execute(select(Client).where(Client.id == job.client_id))).scalar_one()
    site = (await session.execute(select(Site).where(Site.id == job.site_id))).scalar_one()
    return schemas.JobOut(
        id=job.id,
        number=job.number,
        client_id=client.id,
        client_name=client.name,
        site_id=site.id,
        site_label=site.label,
        site_state=site.state,
        client_wo=job.client_wo,
        client_po=job.client_po,
        site_contact=job.site_contact,
        source=job.source,  # type: ignore[arg-type]
        drafted_by=job.drafted_by,  # type: ignore[arg-type]
        issue_type=job.issue_type,
        parts=job.parts,  # type: ignore[arg-type]
        part_numbers=job.part_numbers,
        est_hours=job.est_hours,
        actual_hours=job.actual_hours,
        extenuating=job.extenuating,  # type: ignore[arg-type]
        extenuating_note=job.extenuating_note,
        requires_approval=job.requires_approval,
        rule_fired=job.rule_fired,
        approval=schemas.Approval.model_validate(job.approval) if job.approval else None,
        state=State(job.state),
        queue=QUEUE[State(job.state)],
        owner_id=job.owner_id,
        tech_id=job.tech_id,
        window_start=job.window_start,
        window_end=job.window_end,
        sign_off=schemas.SignOff.model_validate(job.sign_off) if job.sign_off else None,
        estimate_cents=job.estimate_cents,
        final_cents=job.final_cents,
        last_event_id=job.last_event_id,
        updated_at=job.updated_at,
    )


def envelope(event: JobEvent, job_number: int) -> schemas.EventEnvelope:
    return schemas.EventEnvelope(
        id=event.id,
        job_id=event.job_id,
        job_number=job_number,
        at=event.at,
        actor=schemas.Actor(kind=ActorKind(event.actor_kind), person_id=event.actor_id, label=event.actor_label),
        command=event.command,
        from_state=State(event.from_state) if event.from_state else None,
        to_state=State(event.to_state),
        payload=event.payload,
        override_reason=event.override_reason,
    )
