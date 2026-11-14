"""POC-04: commands, the state machine and the rails, run through `commands.execute`."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ofs.commands import Refused, execute, run_system
from ofs.models import Invoice, JobEvent, QbLedger
from ofs.states import TRANSITIONS, Role, State

from .helpers import cmd, event_count, job_in, person, tech_actor

ROLE_PERSON = {Role.COORDINATOR: "Coordinator 1", Role.DISPATCHER: "Dispatcher", Role.CONTROLLER: "Controller"}


@pytest.mark.parametrize("command", sorted(c for c, t in TRANSITIONS.items() if t.roles))
async def test_every_wrong_state_is_refused_and_writes_nothing(seeded: AsyncSession, command: str) -> None:
    t = TRANSITIONS[command]
    for state in set(State) - {s for s in t.sources if s}:
        job = await job_in(seeded, state.value)
        if Role.TECH in t.roles:
            if job.tech_id is None:
                continue  # no tech owns it, so no tech can act on it: covered by the ownership test
            actor = await tech_actor(seeded, job)
        else:
            actor = await person(seeded, ROLE_PERSON[next(iter(t.roles - {Role.TECH}))])
        before, last = await event_count(seeded), job.last_event_id
        with pytest.raises(Refused) as exc:
            await execute(seeded, job.id, cmd(job, command), actor)
        assert exc.value.code == "not_allowed", (command, state)
        # The wrong state is a 409; a tech's 404 is the job not being theirs, which the ownership test covers.
        assert exc.value.status == (404 if Role.TECH in t.roles and exc.value.status == 404 else 409), (command, state)
        if Role.TECH not in t.roles:
            assert exc.value.status == 409 and "while the job is" in exc.value.reason, (command, state)
        assert await event_count(seeded) == before and job.state == state.value and job.last_event_id == last


@pytest.mark.parametrize(
    ("command", "state", "who"),
    [
        ("qualify", "intake_draft", "Dispatcher"),
        ("approve_for_dispatch", "qualified", "Controller"),
        ("assign_tech", "ready_for_dispatch", "Coordinator 1"),
        ("approve_invoice", "billing_review", "Coordinator 1"),
        ("record_payment", "invoiced", "Controller"),  # QuickBooks (simulated) only
    ],
)
async def test_roles_are_enforced(seeded: AsyncSession, command: str, state: str, who: str) -> None:
    job = await job_in(seeded, state)
    with pytest.raises(Refused) as exc:
        await execute(seeded, job.id, cmd(job, command), await person(seeded, who))
    assert exc.value.code == "role" and exc.value.status == 403


async def test_a_tech_acts_only_on_their_own_job(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "assigned")
    owner = await tech_actor(seeded, job)
    other = next(
        a for a in [await person(seeded, f"Tech {i}") for i in range(1, 11)] if a.person and a.person != owner.person
    )
    with pytest.raises(Refused) as exc:
        await execute(seeded, job.id, cmd(job, "arrive"), other)
    assert exc.value.status == 404
    _, events = await execute(seeded, job.id, cmd(job, "arrive"), owner)
    assert job.state == "onsite" and events[0].actor_label == owner.label


async def test_a_stale_view_is_refused(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "intake_draft")
    stale = cmd(job, "qualify")
    stale.expected_event_id -= 1
    with pytest.raises(Refused) as exc:
        await execute(seeded, job.id, stale, await person(seeded, "Coordinator 1"))
    assert exc.value.code == "stale" and exc.value.status == 409


async def test_one_command_one_event_one_transaction(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "intake_draft")
    coord = await person(seeded, "Coordinator 2")
    _, events = await execute(seeded, job.id, cmd(job, "qualify"), coord)
    assert [e.command for e in events] == ["qualify"]
    assert (events[0].from_state, events[0].to_state) == ("intake_draft", "qualified")
    assert job.last_event_id == events[0].id and job.owner_id == coord.person.id  # type: ignore[union-attr]


# --- the hard rails ---


async def test_no_dispatch_over_the_cap_until_the_approval_is_on_record(seeded: AsyncSession) -> None:
    coord = await person(seeded, "Coordinator 1")
    job = await job_in(seeded, "qualified")
    await execute(seeded, job.id, cmd(job, "update_fields", {"estimate_cents": 4_900_000}), coord)
    assert job.requires_approval and job.rule_fired
    for override in (None, "The client said yes on the phone"):
        with pytest.raises(Refused) as exc:
            await execute(seeded, job.id, cmd(job, "approve_for_dispatch", override=override), coord)
        assert exc.value.code == "rail" and job.rule_fired in exc.value.reason
    await execute(seeded, job.id, cmd(job, "request_client_approval"), coord)
    await execute(seeded, job.id, cmd(job, "record_client_approval"), coord)
    assert job.approval and job.approval["client_ref"] == "APR-1"
    await execute(seeded, job.id, cmd(job, "approve_for_dispatch"), coord)
    assert job.state == "ready_for_dispatch"


async def test_no_close_without_a_sign_off_or_a_reason(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "onsite")
    tech = await tech_actor(seeded, job)
    with pytest.raises(Refused) as exc:
        await execute(seeded, job.id, cmd(job, "close_job", {"actual_hours": 2}), tech)
    assert exc.value.code == "rail"
    payload = {"actual_hours": 2, "no_sign_off_reason": "Store manager not on site"}
    _, events = await execute(seeded, job.id, cmd(job, "close_job", payload), tech)
    assert [e.command for e in events] == ["close_job", "draft_invoice"]  # drafted at close
    assert events[1].actor_kind == "system" and job.state == "billing_review"
    invoice = (await seeded.execute(select(Invoice).where(Invoice.job_id == job.id))).scalar_one()
    assert not invoice.check_passed and "sign-off" in (invoice.check_note or "")


async def test_no_approval_for_an_invoice_that_failed_its_check(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "onsite")
    payload = {"actual_hours": 2, "no_sign_off_reason": "Nobody on site"}
    await execute(seeded, job.id, cmd(job, "close_job", payload), await tech_actor(seeded, job))
    controller = await person(seeded, "Controller")
    for override in (None, "Approve it anyway"):
        with pytest.raises(Refused) as exc:
            await execute(seeded, job.id, cmd(job, "approve_invoice", override=override), controller)
        assert exc.value.code == "rail"
    await execute(seeded, job.id, cmd(job, "send_back_invoice"), controller)
    assert job.state == "closed"


# --- the soft rail: overridable, and the override is recorded ---


async def test_assigning_outside_skill_or_license_needs_a_reason(seeded: AsyncSession) -> None:
    from ofs.models import Person, Site, Tech

    job = await job_in(seeded, "ready_for_dispatch")
    site = (await seeded.execute(select(Site).where(Site.id == job.site_id))).scalar_one()
    rows = (await seeded.execute(select(Tech, Person).join(Person, Person.id == Tech.person_id))).all()
    misfit = next(p.label for t, p in rows if site.state not in t.licenses)
    dispatcher = await person(seeded, "Dispatcher")
    with pytest.raises(Refused) as exc:
        await execute(seeded, job.id, cmd(job, "assign_tech", {"tech": misfit}), dispatcher)
    assert exc.value.code == "rail" and site.state in exc.value.reason
    reason = "The licensed tech is out sick; supervised by the lead"
    _, events = await execute(seeded, job.id, cmd(job, "assign_tech", {"tech": misfit}, override=reason), dispatcher)
    assert events[0].override_reason == reason and job.state == "assigned"


# --- the working fields, two-way ---


async def test_fields_edit_two_ways_and_identity_never(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "onsite")
    tech, coord = await tech_actor(seeded, job), await person(seeded, "Coordinator 1")
    _, events = await execute(
        seeded, job.id, cmd(job, "update_fields", {"parts": "special_order", "part_numbers": ["PN-1"]}), tech
    )
    assert events[0].from_state == events[0].to_state == "onsite"
    assert events[0].payload == {"changes": {"parts": "special_order", "part_numbers": ["PN-1"]}}
    with pytest.raises(Refused) as exc:
        await execute(seeded, job.id, cmd(job, "update_fields", {"estimate_cents": 1}), tech)
    assert exc.value.code == "role"
    with pytest.raises(Refused):
        await execute(seeded, job.id, cmd(job, "update_fields", {"client_wo": "X"}), coord)  # part A is fixed
    paid = await job_in(seeded, "paid")
    with pytest.raises(Refused):
        await execute(seeded, paid.id, cmd(paid, "update_fields", {"est_hours": 3}), coord)


async def test_payment_comes_from_quickbooks_simulated(seeded: AsyncSession) -> None:
    job = await job_in(seeded, "invoiced")
    event = await run_system(seeded, job, "record_payment")
    assert job.state == "paid" and event.actor_label == "System"
    inv = (await seeded.execute(select(Invoice).where(Invoice.job_id == job.id))).scalar_one()
    entry = (await seeded.execute(select(QbLedger).where(QbLedger.invoice_id == inv.id))).scalar_one()
    assert entry.paid_at is not None
    assert (await seeded.execute(select(JobEvent).where(JobEvent.id == job.last_event_id))).scalar_one() is event
