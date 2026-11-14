"""POC-04 over HTTP, with real logins: auth, scoping, and the happy path from intake to QuickBooks (simulated)."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ofs.models import QbLedger, User

from .helpers import PASSWORD, job_in, run, sign_in


async def test_login_sets_a_safe_cookie_and_me_answers(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    r = await client.post("/api/auth/login", json={"email": "Coord@ofs.com", "password": PASSWORD})
    assert r.status_code == 200 and r.json()["role"] == "coordinator"
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert (await client.get("/api/auth/me")).json()["label"] == "Coordinator 1"
    await client.post("/api/auth/logout")
    client.cookies.clear()
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_secure_cookie_by_default(
    logins: AsyncSession, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COOKIE_SECURE", "1")
    r = await client.post("/api/auth/login", json={"email": "coord@ofs.com", "password": PASSWORD})
    assert "secure" in r.headers["set-cookie"].lower()


async def test_failures_read_the_same_and_are_rate_limited(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    wrong = await client.post("/api/auth/login", json={"email": "coord@ofs.com", "password": "nope"})
    unknown = await client.post("/api/auth/login", json={"email": "nobody@ofs.com", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401 and wrong.json() == unknown.json()
    codes = [
        (await client.post("/api/auth/login", json={"email": "x@ofs.com", "password": "x"})).status_code
        for _ in range(11)
    ]
    assert codes[:10] == [401] * 10 and codes[10] == 429  # ten tries at one account, then wait


async def test_a_disabled_login_stops_at_once(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    await sign_in(client, "dispatch@ofs.com")
    user = (await logins.execute(select(User).where(User.email == "dispatch@ofs.com"))).scalar_one()
    user.disabled = True
    await logins.flush()
    assert (await client.get("/api/jobs")).status_code == 401


async def test_exec_reads_everything_and_changes_nothing(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    await sign_in(client, "exec@ofs.com")
    assert len((await client.get("/api/jobs")).json()) == 45
    job = await job_in(logins, "intake_draft")
    assert (await run(client, job.id, "qualify")).status_code == 403


async def test_a_cross_site_post_is_refused(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    await sign_in(client, "coord@ofs.com")
    job = await job_in(logins, "intake_draft")
    body = {"command": "qualify", "expected_event_id": job.last_event_id, "payload": {}}
    r = await client.post(f"/api/jobs/{job.id}/commands", json=body, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


async def test_a_tech_sees_only_their_queue(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    await sign_in(client, "tech@ofs.com")
    me = (await client.get("/api/auth/me")).json()
    jobs = (await client.get("/api/jobs")).json()
    assert len(jobs) < 45
    other = await job_in(logins, "paid")
    if other.id not in {j["id"] for j in jobs}:
        assert (await client.get(f"/api/jobs/{other.id}")).status_code == 404
    assert me["role"] == "tech" and me["tech_id"]
    assert all(j["tech_id"] == me["tech_id"] for j in jobs)  # the phone's scope is the tech's own id


async def test_queues_and_mine_filter(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    await sign_in(client, "coord@ofs.com")
    billing = (await client.get("/api/jobs", params={"queue": "billing"})).json()
    assert billing and {j["state"] for j in billing} <= {"closed", "billing_review"}
    mine = (await client.get("/api/jobs", params={"mine": True})).json()
    me = (await client.get("/api/auth/me")).json()
    assert all(j["owner_id"] == me["person_id"] for j in mine)


async def test_the_happy_path_end_to_end(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    """N1 to N3 (plan §11): one job, intake to QuickBooks (simulated), each step by its own role."""
    job = await job_in(logins, "intake_draft", requires_approval=False)

    await sign_in(client, "coord@ofs.com")
    assert (await run(client, job.id, "qualify")).status_code == 200
    r = await run(client, job.id, "approve_for_dispatch")
    assert r.json()["job"]["state"] == "ready_for_dispatch"

    await sign_in(client, "dispatch@ofs.com")
    r = await run(client, job.id, "assign_tech", {"tech": "Tech 1"}, override_reason="Tech 1 covers the demo route")
    assert r.status_code == 200, r.text
    assert r.json()["job"]["state"] == "assigned"

    await sign_in(client, "tech@ofs.com")
    assert str(job.id) in {j["id"] for j in (await client.get("/api/jobs")).json()}  # T1: it's on my schedule
    assert (await run(client, job.id, "arrive")).json()["job"]["state"] == "onsite"
    assert (await run(client, job.id, "update_fields", {"parts": "on_truck"})).status_code == 200
    r = await run(client, job.id, "close_job", {"actual_hours": 3.0, "sign_off_by": "Store manager"})
    assert [e["command"] for e in r.json()["events"]] == ["close_job", "draft_invoice"]
    assert r.json()["job"]["state"] == "billing_review"

    await sign_in(client, "controller@ofs.com")
    r = await run(client, job.id, "approve_invoice")
    assert r.status_code == 200, r.text
    doc = r.json()["events"][0]["payload"]["qb_doc_number"]
    assert r.json()["job"]["state"] == "invoiced"
    entry = (await logins.execute(select(QbLedger).where(QbLedger.doc_number == doc))).scalar_one()
    assert entry.paid_at is None and entry.amount_cents == r.json()["job"]["final_cents"]

    history = (await client.get(f"/api/jobs/{job.id}/events")).json()
    assert [e["command"] for e in history] == [
        "draft_intake",
        "qualify",
        "approve_for_dispatch",
        "assign_tech",
        "arrive",
        "update_fields",
        "close_job",
        "draft_invoice",
        "approve_invoice",
    ]
    assert [e["actor"]["label"] for e in history] == [
        "System",
        "Coordinator 1",
        "Coordinator 1",
        "Dispatcher",
        "Tech 1",
        "Tech 1",
        "Tech 1",
        "System",
        "Controller",
    ]
    assert [e["id"] for e in history] == sorted(e["id"] for e in history)


async def test_the_overview_counts_every_job_and_times_every_step(
    logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    """G3 and Q9: the counts match the jobs; the waits come from the history, and a tech can't see it."""
    from collections import Counter

    from ofs.models import Job

    await sign_in(client, "exec@ofs.com")
    body = (await client.get("/api/overview")).json()
    states = Counter((await logins.execute(select(Job.state))).scalars())
    assert body["total"] == 45
    assert {s["state"]: s["open"] for s in body["steps"] if s["open"]} == dict(states)
    assert [s["state"] for s in body["steps"]][:2] == ["intake_draft", "qualified"]
    qualify = next(s for s in body["steps"] if s["state"] == "intake_draft")
    assert qualify["done"] > 0 and qualify["done_hours_median"] > 0
    await sign_in(client, "tech@ofs.com")
    assert (await client.get("/api/overview")).status_code == 403


async def test_no_schema_is_served(client: httpx.AsyncClient) -> None:
    assert (await client.get("/openapi.json")).status_code == 404
    assert (await client.get("/docs")).status_code == 404


async def test_every_ready_job_has_a_recommendation_that_fits(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    """D2 over HTTP: the top tech has the skill and the license for the site's state, and says so."""
    from ofs.models import Job, Site

    await sign_in(client, "dispatch@ofs.com")
    roster = {t["id"]: t for t in (await client.get("/api/techs")).json()}
    ready = (
        await logins.execute(
            select(Job, Site).join(Site, Site.id == Job.site_id).where(Job.state == "ready_for_dispatch")
        )
    ).all()
    assert ready
    for job, site in ready:
        rec = (await client.get(f"/api/jobs/{job.id}/recommendation")).json()
        top = rec["top"]
        assert top and top["eligible"] and len(rec["candidates"]) == len(roster)
        tech = roster[top["tech_id"]]
        assert job.issue_type in tech["skills"] and site.state in tech["licenses"]
        assert f"Licensed in {site.state}" in top["reasons"]


async def test_the_roster_counts_each_techs_board(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    from ofs.models import Job

    await sign_in(client, "dispatch@ofs.com")
    roster = (await client.get("/api/techs")).json()
    on_board = await logins.scalar(
        select(func.count()).select_from(Job).where(Job.state.in_(("assigned", "onsite", "needs_review")))
    )
    assert len(roster) == 10 and sum(t["load"] for t in roster) == on_board
    assert [t["label"] for t in roster][:3] == ["Tech 1", "Tech 2", "Tech 3"]
    await sign_in(client, "tech@ofs.com")
    assert (await client.get("/api/techs")).status_code == 403


async def test_one_address_cant_sweep_many_accounts(logins: AsyncSession, client: httpx.AsyncClient) -> None:
    codes = [
        (await client.post("/api/auth/login", json={"email": f"u{i}@ofs.com", "password": "x"})).status_code
        for i in range(61)
    ]
    assert codes[:60] == [401] * 60 and codes[60] == 429


async def test_the_controller_sees_the_drafted_invoice_and_its_check(
    logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    from ofs.models import Job

    await sign_in(client, "controller@ofs.com")
    job = (await logins.execute(select(Job).where(Job.state == "billing_review").limit(1))).scalar_one()
    inv = (await client.get(f"/api/jobs/{job.id}/invoice")).json()
    assert inv["state"] == "draft" and inv["total_cents"] == sum(line["cents"] for line in inv["lines"])
    assert isinstance(inv["check_passed"], bool) and (inv["check_passed"] or inv["check_note"])
    draft = (await logins.execute(select(Job).where(Job.state == "intake_draft").limit(1))).scalar_one()
    assert (await client.get(f"/api/jobs/{draft.id}/invoice")).status_code == 404
    await sign_in(client, "dispatch@ofs.com")
    assert (await client.get(f"/api/jobs/{job.id}/invoice")).status_code == 403


async def test_aging_buckets_every_open_invoice_and_approval_moves_it(
    logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    """B2 and B3: approving a checked invoice posts it to QuickBooks (simulated), and it shows as Current."""
    from ofs.models import Invoice, Job, QbLedger

    await sign_in(client, "controller@ofs.com")
    before = (await client.get("/api/qb/aging")).json()
    assert [b["label"] for b in before["buckets"]] == ["Current", "1 to 30", "31 to 60", "61 to 90", "Over 90"]
    assert all(b["count"] > 0 for b in before["buckets"])  # the seed fills every bucket
    assert sum(b["count"] for b in before["buckets"]) == before["open_count"]
    assert before["open_count"] == await logins.scalar(
        select(func.count()).select_from(QbLedger).where(QbLedger.paid_at.is_(None))
    )
    job = (
        await logins.execute(
            select(Job)
            .join(Invoice, Invoice.job_id == Job.id)
            .where(Job.state == "billing_review", Invoice.check_passed.is_(True))
            .limit(1)
        )
    ).scalar_one()
    r = await run(client, job.id, "approve_invoice")
    assert r.status_code == 200, r.text
    after = (await client.get("/api/qb/aging")).json()
    assert after["buckets"][0]["count"] == before["buckets"][0]["count"] + 1
    assert after["open_cents"] - before["open_cents"] == r.json()["job"]["final_cents"]
    await sign_in(client, "coord@ofs.com")
    assert (await client.get("/api/qb/aging")).status_code == 403
