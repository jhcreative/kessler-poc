"""POC-04 over HTTP, with real logins: auth, scoping, and the happy path from intake to QuickBooks (simulated)."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import select
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
        for _ in range(10)
    ]
    assert codes[-1] == 429


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
    assert me["role"] == "tech"


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
