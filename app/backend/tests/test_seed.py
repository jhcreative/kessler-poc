"""POC-03 acceptance: 45 jobs over every state, each with a history the state table allows."""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Any

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ofs.models import STATES_SEVEN, Client, Contract, Invoice, Job, JobEvent, QbLedger, Site, Tech
from ofs.rules import evaluate
from ofs.seed import AGING_BUCKETS, JOBS_BY_STATE, seed
from ofs.states import State, allowed

from .conftest import NOW


async def _dump(session: AsyncSession) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for table in (
        "clients",
        "sites",
        "people",
        "techs",
        "jobs",
        "job_events",
        "invoices",
        "qb_ledger",
    ):
        rows = (await session.execute(text(f"SELECT * FROM {table} ORDER BY 1"))).all()  # noqa: S608
        out[table] = [tuple(r) for r in rows]
    return out


async def test_counts(session: AsyncSession) -> None:
    counts = await seed(session, now=NOW)
    assert counts["clients"] == 8
    assert counts["sites"] == 60
    assert counts["techs"] == 10
    assert counts["jobs"] == 45
    assert counts["people"] == 16


async def test_every_state_is_on_the_board(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    states = Counter((await session.execute(select(Job.state))).scalars())
    assert {State(s): n for s, n in states.items()} == JOBS_BY_STATE


async def test_every_history_is_legal_ordered_and_ends_at_the_job(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    for job in (await session.execute(select(Job))).scalars():
        events = (
            (await session.execute(select(JobEvent).where(JobEvent.job_id == job.id).order_by(JobEvent.id)))
            .scalars()
            .all()
        )
        current = None
        for e in events:
            assert allowed(e.command, State(e.from_state) if e.from_state else None)
            assert e.from_state == current
            current = e.to_state
        assert current == job.state
        assert [e.at for e in events] == sorted(e.at for e in events)
        assert events[-1].at <= NOW
        assert job.last_event_id == events[-1].id


async def test_rails_hold_in_the_seed(session: AsyncSession) -> None:
    """The three hard rails (plan §4) are already true of the data the demo starts from."""
    await seed(session, now=NOW)
    contracts = {c.client_id: c for c in (await session.execute(select(Contract))).scalars()}
    dispatched = {s.value for s in State} - {"intake_draft", "qualified", "needs_client_approval"}
    for job in (await session.execute(select(Job))).scalars():
        assert (job.requires_approval, job.rule_fired) == evaluate(
            contracts[job.client_id].rules, job.issue_type, job.estimate_cents
        )
        if job.requires_approval and job.state in dispatched:
            assert job.approval and job.approval["client_ref"]  # no dispatch over the cap without it
        if job.state in ("closed", "billing_review", "invoiced", "paid"):
            assert job.sign_off or job.extenuating_note  # no close without a sign-off or a reason
    for inv in (await session.execute(select(Invoice).where(Invoice.state == "submitted"))).scalars():
        assert inv.check_passed  # no approved invoice that failed the check


async def test_dispatch_always_has_someone_to_recommend(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    techs = (await session.execute(select(Tech))).scalars().all()
    ready = (
        await session.execute(
            select(Job, Site).join(Site, Site.id == Job.site_id).where(Job.state == "ready_for_dispatch")
        )
    ).all()
    assert ready
    for job, site in ready:
        assert any(job.issue_type in t.skills and site.state in t.licenses for t in techs)


async def test_sites_sit_in_the_seven_states(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    assert set((await session.execute(select(Site.state))).scalars()) <= set(STATES_SEVEN)


async def test_aging_has_every_bucket(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    open_rows = (await session.execute(select(QbLedger).where(QbLedger.paid_at.is_(None)))).scalars().all()
    for low, high in AGING_BUCKETS:
        lo, hi = NOW - timedelta(days=high + 1), NOW - timedelta(days=low - 1)
        assert any(lo < r.due_at < hi for r in open_rows), (low, high)
    assert len((await session.execute(select(QbLedger))).scalars().all()) >= 150


async def test_same_seed_same_world(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    first = await _dump(session)
    await seed(session, now=NOW)
    assert await _dump(session) == first


async def test_fictional_names_and_facilit_as_a_channel(session: AsyncSession) -> None:
    await seed(session, now=NOW)
    clients = (await session.execute(select(Client))).scalars().all()
    assert "Bullseye" in {c.name for c in clients}
    assert "FacilIT" not in {c.name for c in clients}  # a channel, not a client
    assert {c.channel for c in clients} == {"portal", "email", "facilit"}


async def test_health_counts_the_seed(session: AsyncSession, client: httpx.AsyncClient) -> None:
    counts = await seed(session, now=NOW)
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"jobs": 45, "events": counts["job_events"]}


async def test_a_few_jobs_need_approval_not_most(session: AsyncSession) -> None:
    """Plan §7: "a few sit over the cap". The happy path must be the common case."""
    await seed(session, now=NOW)
    flags = (await session.execute(select(Job.requires_approval))).scalars().all()
    assert 3 <= sum(flags) <= 12, sum(flags)
    drafts = (await session.execute(select(Job).where(Job.state == "intake_draft"))).scalars().all()
    assert any(not j.requires_approval for j in drafts)  # N1 starts from one of these
    cents = (await session.execute(select(Job.estimate_cents))).scalars().all()
    assert min(cents) >= 200_000 and max(cents) <= 5_000_000


async def test_every_seeded_invoice_prices_its_hours_at_one_rate(session: AsyncSession) -> None:
    """The seed's invoices are drafted the way the backend drafts them: hours at the rate, the rest parts."""
    from ofs.commands import LABOR_RATE_CENTS

    await seed(session, now=NOW)
    rows = (await session.execute(select(Invoice, Job).join(Job, Job.id == Invoice.job_id))).all()
    assert rows
    for inv, job in rows:
        (labor, parts) = inv.lines
        assert labor["desc"] == f"Labor, {job.actual_hours} h" and parts["desc"] == "Parts and materials"
        assert labor["cents"] == min(round(job.actual_hours * LABOR_RATE_CENTS), inv.total_cents)
        assert parts["cents"] == inv.total_cents - labor["cents"] >= 0
