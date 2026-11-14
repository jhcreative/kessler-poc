"""The WebSocket: `/api/ws?after=<last event id>` (plan §4, POC-05).

Server to view, JSON, one message per frame:

  {"type": "hello", "last_event_id": N}        sent first, after any replay
  {"type": "event", "event": {...}, "job": {...}}  EventEnvelope and the job as it now is (JobOut)
  {"type": "ping"}                              every 25 s, so no proxy closes an idle socket (risk R1)
  {"type": "resync"}                            too far behind: reload the lists, then reconnect

No missed updates, no duplicates. The socket subscribes to the hub BEFORE it reads the replay from `job_events`, so
nothing committed in between is lost. Then it sends the replay, and drops any live message whose id it has already
sent.

What this defends against, and how:
- Someone without a login: the session cookie is checked at the upgrade (close 4401).
- Another site opening a socket with the user's cookie (cross-site WebSocket hijacking): browsers always send Origin
  on a WebSocket, and it must be one of ours (close 4403).
- A tech reading other techs' jobs: the hub filters by role on the server, and so does the replay.
- A login removed while its socket is open: the account is re-checked every 25 s, busy or idle (close 4401).
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import false, select

from .auth import COOKIE, Caller, allowed_origins, caller_for
from .commands import envelope, job_out
from .db import open_session
from .hub import hub
from .models import Job, JobEvent, Tech
from .schemas import JobOut, LiveEvent, LiveHello, LivePing, LiveResync
from .states import Role

router = APIRouter()

PING_SECONDS = 25.0
REPLAY_LIMIT = 1000


async def _tech_id(caller: Caller) -> Any:
    async with open_session() as session:
        return await session.scalar(select(Tech.id).where(Tech.person_id == caller.person.id))


async def _replay(caller: Caller, tech_id: Any, after: int) -> list[dict[str, Any]] | None:
    """Everything after `after` that this caller may see, oldest first; None if it's too much to replay."""
    async with open_session() as session:
        q = select(JobEvent, Job).join(Job, Job.id == JobEvent.job_id).where(JobEvent.id > after)
        if caller.role is Role.TECH:
            q = q.where(Job.tech_id == tech_id) if tech_id else q.where(false())
        rows = (await session.execute(q.order_by(JobEvent.id).limit(REPLAY_LIMIT + 1))).all()
        if len(rows) > REPLAY_LIMIT:
            return None
        jobs: dict[Any, JobOut] = {}
        out = []
        for event, job in rows:
            if job.id not in jobs:
                jobs[job.id] = await job_out(session, job)
            out.append(LiveEvent(event=envelope(event, job.number), job=jobs[job.id]).model_dump(mode="json"))
        return out


async def _last_id() -> int:
    async with open_session() as session:
        return int(await session.scalar(select(JobEvent.id).order_by(JobEvent.id.desc()).limit(1)) or 0)


async def _until_gone(ws: WebSocket) -> None:
    """Returns when the view disconnects. Views send nothing; anything they do send is ignored."""
    while (await ws.receive())["type"] != "websocket.disconnect":
        pass


@router.websocket("/api/ws")
async def socket(ws: WebSocket, after: int | None = None) -> None:
    # Accept, then close with a code, so the view can tell "sign in" from "refused" (a refusal before accept is a
    # bare HTTP 403). Nothing is sent before the checks pass.
    await ws.accept()
    if ws.headers.get("origin") not in allowed_origins():
        await ws.close(code=4403, reason="Cross-site socket refused")
        return
    async with open_session() as session:
        caller = await caller_for(session, ws.cookies.get(COOKIE))
    if caller is None:
        await ws.close(code=4401, reason="Sign in first")
        return
    tech_id = await _tech_id(caller) if caller.role is Role.TECH else None
    sub = hub.subscribe(caller.role, tech_id)  # before the replay: nothing can fall in the gap
    try:
        sent = after if after is not None else await _last_id()
        if after is not None:
            replay = await _replay(caller, tech_id, after)
            if replay is None:
                await ws.send_json(LiveResync().model_dump())
                await ws.close(code=4409, reason="Too far behind; reload")
                return
            for msg in replay:
                await ws.send_json(msg)
                sent = max(sent, msg["event"]["id"])
        await ws.send_json(LiveHello(last_event_id=sent).model_dump())
        gone = asyncio.create_task(_until_gone(ws))  # notice a closed view at once, not at the next ping
        checked = time.monotonic()
        while True:
            # The login is re-checked every PING_SECONDS, busy or idle (cold review, finding 5): a disabled or expired
            # session stops hearing events even when events never stop.
            if time.monotonic() - checked >= PING_SECONDS:
                async with open_session() as session:
                    if await caller_for(session, ws.cookies.get(COOKIE)) is None:
                        await ws.close(code=4401, reason="Your session has ended")
                        return
                checked = time.monotonic()
            get = asyncio.create_task(sub.queue.get())
            done, _ = await asyncio.wait({get, gone}, timeout=PING_SECONDS, return_when=asyncio.FIRST_COMPLETED)
            if gone in done:
                get.cancel()
                return
            if get not in done:
                get.cancel()
                await ws.send_json(LivePing().model_dump())
                continue
            msg = get.result()
            if sub.overflowed:
                await ws.send_json(LiveResync().model_dump())
                await ws.close(code=4409, reason="Too far behind; reload")
                return
            if msg["event"]["id"] <= sent:
                continue  # already sent in the replay
            await ws.send_json(msg)
            sent = msg["event"]["id"]
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(sub)
        if "gone" in locals():
            gone.cancel()
        with contextlib.suppress(Exception):
            await ws.close()
