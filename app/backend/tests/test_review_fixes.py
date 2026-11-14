"""The cold review's findings (POC-11, DOD-3), each pinned by a test that fails without its fix."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ofs import intake
from ofs.commands import Refused, execute, invoice_check
from ofs.models import FleetPosition, Invoice, Job, Person, Tech, User
from ofs.seed import seed

from .conftest import NOW
from .helpers import PASSWORD, cmd, job_in, person, run, sign_in, tech_actor

# --- 7. Two people move the same job at once: the row lock makes the second wait, then see it's stale. ---


@pytest.fixture
async def committed(engine: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    """A world committed for real, so two separate sessions can race over it. Emptied afterwards."""
    async with AsyncSession(engine) as s:
        await seed(s, now=NOW)
        await s.commit()
    yield engine
    async with AsyncSession(engine) as s:
        await s.execute(
            text(
                "TRUNCATE qb_ledger, invoices, job_events, jobs, fleet_positions, techs, people, sites, "
                "contracts, clients RESTART IDENTITY CASCADE"
            )
        )
        await s.commit()


async def test_two_people_racing_one_job_one_wins_one_is_told_its_stale(committed: AsyncEngine) -> None:
    async with AsyncSession(committed) as first, AsyncSession(committed) as second:
        job = (await first.execute(select(Job).where(Job.state == "intake_draft").limit(1))).scalar_one()
        job_id, seen = job.id, job.last_event_id
        both_saw = cmd(job, "qualify")
        assert both_saw.expected_event_id == seen
        await execute(first, job_id, both_saw, await person(first, "Coordinator 1"))  # holds the row lock
        racer = asyncio.create_task(execute(second, job_id, both_saw, await person(second, "Coordinator 2")))
        await asyncio.sleep(0.3)
        assert not racer.done()  # waiting on the lock, not reading the old row
        await first.commit()
        with pytest.raises(Refused) as exc:
            await racer
        assert exc.value.code == "stale"
        await second.rollback()
        events = (
            await first.execute(
                text("SELECT count(*) FROM job_events WHERE job_id = :j AND command = 'qualify'"), {"j": job_id}
            )
        ).scalar_one()
        assert events == 1


# --- 3. What the dispatch rail checks can't move after dispatch; an approval covers its amount. ---


async def test_the_priced_fields_are_the_coordinators_and_fixed_once_dispatched(seeded: AsyncSession) -> None:
    onsite = await job_in(seeded, "onsite")
    with pytest.raises(Refused) as exc:
        await execute(
            seeded, onsite.id, cmd(onsite, "update_fields", {"issue_type": "general"}), await tech_actor(seeded, onsite)
        )
    assert exc.value.code == "role"
    ready = await job_in(seeded, "ready_for_dispatch")
    with pytest.raises(Refused) as exc:
        await execute(
            seeded,
            ready.id,
            cmd(ready, "update_fields", {"estimate_cents": 4_900_000}),
            await person(seeded, "Coordinator 1"),
        )
    assert exc.value.code == "rail"


async def test_raising_the_estimate_voids_the_approval(seeded: AsyncSession) -> None:
    coord = await person(seeded, "Coordinator 1")
    job = await job_in(seeded, "qualified")
    await execute(seeded, job.id, cmd(job, "update_fields", {"estimate_cents": 4_000_000}), coord)
    await execute(seeded, job.id, cmd(job, "request_client_approval"), coord)
    await execute(seeded, job.id, cmd(job, "record_client_approval"), coord)
    assert job.approval
    await execute(seeded, job.id, cmd(job, "update_fields", {"estimate_cents": 4_800_000}), coord)
    assert job.approval is None
    with pytest.raises(Refused):
        await execute(seeded, job.id, cmd(job, "approve_for_dispatch"), coord)


# --- 6 and 18. The seed agrees with the backend's own check, and trucks stand where techs work. ---


async def test_every_seeded_invoice_carries_the_backends_own_check(seeded: AsyncSession) -> None:
    rows = (await seeded.execute(select(Invoice, Job).join(Job, Job.id == Invoice.job_id))).all()
    assert rows
    for invoice, job in rows:
        assert invoice.check_note == invoice_check(job) and invoice.check_passed == (invoice.check_note is None)
        if invoice.state == "submitted":
            assert invoice.check_passed
        if job.state == "closed":
            assert not invoice.check_passed and invoice.state == "sent_back"


async def test_a_tech_on_site_has_the_truck_at_the_site(seeded: AsyncSession) -> None:
    from ofs.models import Site

    rows = (
        await seeded.execute(
            select(Job, Site, FleetPosition)
            .join(Site, Site.id == Job.site_id)
            .join(Tech, Tech.id == Job.tech_id)
            .join(FleetPosition, FleetPosition.truck == Tech.truck)
            .where(Job.state == "onsite")
        )
    ).all()
    assert rows
    for _job, site, pos in rows:
        assert (pos.lat, pos.lng, pos.status) == (site.lat, site.lng, "onsite")


# --- 11, 13, 15, 16, 17. ---


async def test_a_long_password_is_a_401_not_a_500(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    r = await client.post("/api/auth/login", json={"email": "coord@ofs.com", "password": PASSWORD + "x" * 80})
    assert r.status_code == 401


async def test_a_tech_login_without_a_tech_record_sees_nothing(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    from ofs.auth import hash_password

    logins.add(Person(label="Tech 99", role="tech", email="tech99@ofs.com"))
    logins.add(User(email="tech99@ofs.com", password_hash=hash_password(PASSWORD)))
    await logins.flush()
    await sign_in(client, "tech99@ofs.com")
    assert (await client.get("/api/jobs")).json() == []  # not every unassigned job (IS NULL)


async def test_new_requests_are_throttled_per_person(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    from ofs import api

    api._last_request.clear()
    await sign_in(client, "coord@ofs.com")
    assert (await client.post("/api/intake/simulate")).status_code == 200
    assert (await client.post("/api/intake/simulate")).status_code == 429


async def test_any_claude_failure_falls_back_to_the_rules(
    seeded: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Broken:
        class beta:  # noqa: N801
            class messages:  # noqa: N801
                @staticmethod
                async def parse(**_: object) -> None:
                    raise ValueError("a malformed response")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-used")
    monkeypatch.setattr(intake, "_client", Broken())
    d = await intake.claude_drafter("Bullseye store #1735: lights out. Work order: BE-WO-123456", ["Bullseye"])
    assert d.by == "rules" and d.fallback_reason == "Claude's draft failed (ValueError)"


async def test_the_cookie_is_secure_unless_told_otherwise(
    logins: AsyncSession, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("COOKIE_SECURE", raising=False)  # the box's default, not a value the test chose
    r = await client.post("/api/auth/login", json={"email": "coord@ofs.com", "password": PASSWORD})
    assert "secure" in r.headers["set-cookie"].lower()


async def test_logout_tells_the_browser_to_drop_the_cookie(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    await sign_in(client, "coord@ofs.com")
    r = await client.post("/api/auth/logout")
    assert r.status_code == 204
    dropped = r.headers["set-cookie"].lower()
    assert dropped.startswith("ofs_session=") and ("max-age=0" in dropped or "expires=thu, 01 jan 1970" in dropped)
    assert "ofs_session" not in client.cookies  # because the server said so, not because the test cleared it
    assert (await client.get("/api/auth/me")).status_code == 401


# --- 9. A commit that fails publishes nothing. ---


async def test_a_failed_commit_publishes_nothing(
    logins: AsyncSession, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ofs.hub import hub

    heard: list[object] = []
    monkeypatch.setattr(hub, "publish", lambda messages: heard.extend(messages))
    await sign_in(client, "coord@ofs.com")
    job = await job_in(logins, "intake_draft")

    async def broken_commit() -> None:
        raise RuntimeError("the database went away at commit")

    monkeypatch.setattr(logins, "commit", broken_commit)
    with pytest.raises(RuntimeError):
        await run(client, job.id, "qualify")
    assert heard == []
