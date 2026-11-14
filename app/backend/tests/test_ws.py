"""POC-05 against a real server: uvicorn in the test's loop, real WebSocket clients, real session cookies."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
import uvicorn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from ofs import ws as ws_module
from ofs.main import app
from ofs.models import Job, Person, Tech

from .helpers import job_in, run, sign_in

ORIGIN = "http://localhost:9219"
Opener = Callable[..., Any]


@pytest.fixture
async def server(logins: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[str]:
    @asynccontextmanager
    async def _test_session() -> AsyncIterator[AsyncSession]:
        yield logins

    monkeypatch.setattr(ws_module, "open_session", _test_session)
    monkeypatch.setattr(ws_module, "PING_SECONDS", 60.0)
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, lifespan="off", log_level="warning"))
    task = asyncio.create_task(srv.serve())
    while not srv.started:  # noqa: ASYNC110 (uvicorn exposes a flag, not an event)
        await asyncio.sleep(0.01)
    port = srv.servers[0].sockets[0].getsockname()[1]
    yield f"ws://127.0.0.1:{port}/api/ws"
    srv.should_exit = True
    await task


def opener(url: str, cookie: str | None, origin: str = ORIGIN) -> Any:
    headers = {"Origin": origin, **({"Cookie": f"ofs_session={cookie}"} if cookie else {})}
    return connect(url, additional_headers=headers)


async def recv(sock: ClientConnection, within: float = 1.0) -> dict[str, Any]:
    return dict(json.loads(await asyncio.wait_for(sock.recv(), within)))


async def silent(sock: ClientConnection, seconds: float = 0.3) -> bool:
    try:
        await asyncio.wait_for(sock.recv(), seconds)
    except TimeoutError:
        return True
    return False


async def test_a_change_in_one_view_reaches_another_within_a_second(
    server: str, logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    """G1, shown: the coordinator watches; the dispatcher assigns; the coordinator's view hears it."""
    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(server, cookie) as coord:
        assert (await recv(coord))["type"] == "hello"
        job = await job_in(logins, "ready_for_dispatch")
        await sign_in(client, "dispatch@ofs.com")
        started = time.monotonic()
        r = await run(client, job.id, "assign_tech", {"tech": "Tech 1"}, override_reason="Demo route")
        assert r.status_code == 200, r.text
        msg = await recv(coord)
        assert time.monotonic() - started < 1.0
        assert msg["type"] == "event" and msg["event"]["command"] == "assign_tech"
        assert msg["job"]["id"] == str(job.id) and msg["job"]["state"] == "assigned"
        assert msg["event"]["actor"]["label"] == "Dispatcher"


async def test_reconnect_replays_what_was_missed_with_no_gap_and_no_duplicate(
    server: str, logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(server, cookie) as first:
        last = (await recv(first))["last_event_id"]
    a, b = await job_in(logins, "intake_draft"), await job_in(logins, "qualified")
    assert (await run(client, a.id, "qualify")).status_code == 200  # while the view is away
    assert (await run(client, b.id, "update_fields", {"est_hours": 5.5})).status_code == 200
    async with opener(f"{server}?after={last}", cookie) as again:
        replayed = [await recv(again), await recv(again)]
        hello = await recv(again)
        assert [m["event"]["command"] for m in replayed] == ["qualify", "update_fields"]
        ids = [m["event"]["id"] for m in replayed]
        assert ids == sorted(ids) and ids[0] > last and hello == {"type": "hello", "last_event_id": ids[-1]}
        assert (await run(client, a.id, "approve_for_dispatch")).status_code == 200
        live = await recv(again)
        assert live["event"]["id"] > ids[-1] and live["event"]["command"] == "approve_for_dispatch"
        assert await silent(again)  # nothing twice


async def test_a_tech_hears_only_their_own_jobs(server: str, logins: AsyncSession, client: httpx.AsyncClient) -> None:
    cookie = await sign_in(client, "tech@ofs.com")
    async with opener(server, cookie) as tech:
        await recv(tech)
        await sign_in(client, "coord@ofs.com")
        draft = await job_in(logins, "intake_draft")
        assert (await run(client, draft.id, "qualify")).status_code == 200
        assert await silent(tech)  # not theirs
        await sign_in(client, "dispatch@ofs.com")
        ready = await job_in(logins, "ready_for_dispatch")
        await run(client, ready.id, "assign_tech", {"tech": "Tech 1"}, override_reason="Demo route")
        msg = await recv(tech)  # T1: a new job arrives on their schedule
        assert msg["job"]["id"] == str(ready.id) and msg["job"]["state"] == "assigned"


async def test_a_techs_replay_is_their_own_jobs_only(
    server: str, logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    tech1 = (
        await logins.execute(select(Tech).join(Person, Person.id == Tech.person_id).where(Person.label == "Tech 1"))
    ).scalar_one()
    theirs = {str(j) for j in (await logins.execute(select(Job.id).where(Job.tech_id == tech1.id))).scalars()}
    cookie = await sign_in(client, "tech@ofs.com")
    async with opener(f"{server}?after=0", cookie) as tech:
        seen = set()
        while (msg := await recv(tech))["type"] == "event":
            seen.add(msg["job"]["id"])
        assert seen == theirs


async def test_a_refused_command_publishes_nothing(
    server: str, logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(server, cookie) as coord:
        await recv(coord)
        job = await job_in(logins, "intake_draft")
        r = await run(client, job.id, "approve_for_dispatch")  # not from intake_draft
        assert r.status_code == 409
        assert await silent(coord)


async def test_no_cookie_and_another_sites_origin_are_refused(server: str, client: httpx.AsyncClient) -> None:
    async with opener(server, None) as anon:
        with pytest.raises(ConnectionClosed) as exc:
            await anon.recv()
        assert exc.value.rcvd is not None and exc.value.rcvd.code == 4401
    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(server, cookie, origin="https://evil.example") as hijack:
        with pytest.raises(ConnectionClosed) as exc:
            await hijack.recv()
        assert exc.value.rcvd is not None and exc.value.rcvd.code == 4403


async def test_too_far_behind_is_told_to_reload(
    server: str, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ws_module, "REPLAY_LIMIT", 5)
    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(f"{server}?after=0", cookie) as late:
        assert (await recv(late)) == {"type": "resync"}
        with pytest.raises(ConnectionClosed) as exc:
            await late.recv()
        assert exc.value.rcvd is not None and exc.value.rcvd.code == 4409


async def test_an_idle_socket_is_pinged_and_rechecked(
    server: str, logins: AsyncSession, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ofs.models import User

    monkeypatch.setattr(ws_module, "PING_SECONDS", 0.2)
    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(server, cookie) as coord:
        await recv(coord)
        assert await recv(coord) == {"type": "ping"}
        user = (await logins.execute(select(User).where(User.email == "coord@ofs.com"))).scalar_one()
        user.disabled = True
        await logins.flush()
        with pytest.raises(ConnectionClosed) as exc:
            await coord.recv()
            await coord.recv()
        assert exc.value.rcvd is not None and exc.value.rcvd.code == 4401


async def test_a_closed_view_leaves_the_hub_at_once(server: str, client: httpx.AsyncClient) -> None:
    from ofs.hub import hub

    cookie = await sign_in(client, "coord@ofs.com")
    async with opener(server, cookie) as coord:
        await recv(coord)
        assert hub.size == 1
    for _ in range(50):  # well under the 60 s ping this server runs with
        if hub.size == 0:
            break
        await asyncio.sleep(0.02)
    assert hub.size == 0
