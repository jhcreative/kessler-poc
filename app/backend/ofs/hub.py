"""The in-process hub: after a commit, every open view hears about the change (G1).

One uvicorn process serves the app, so the hub is a set of in-memory queues, and no broker is needed (plan §4). Each
message carries the `job_events.id`; a view that reconnects asks for everything after its last id (`ws.py`), so a
dropped connection never leaves it showing a stale job.

Who hears what is decided here, on the server. A tech hears only about jobs that are, or just stopped being, theirs.
Everyone else hears everything. The exec's view is read-only, but it still needs the overview to move.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

from .states import Role

QUEUE_LIMIT = 1000  # a view this far behind is told to reload rather than flooded


@dataclass(eq=False)
class Subscriber:
    role: Role
    tech_id: uuid.UUID | None
    queue: asyncio.Queue[dict[str, Any]] = field(default_factory=lambda: asyncio.Queue(QUEUE_LIMIT))
    overflowed: bool = False


@dataclass(frozen=True)
class Message:
    body: dict[str, Any]  # {"type": "event", "event": EventEnvelope, "job": JobOut}, JSON-ready
    techs: frozenset[uuid.UUID]  # the job's tech before and after the change


class Hub:
    def __init__(self) -> None:
        self._subs: set[Subscriber] = set()

    def subscribe(self, role: Role, tech_id: uuid.UUID | None) -> Subscriber:
        sub = Subscriber(role=role, tech_id=tech_id)
        self._subs.add(sub)
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        self._subs.discard(sub)

    @property
    def size(self) -> int:
        return len(self._subs)

    def publish(self, messages: list[Message]) -> None:
        """Called only after the transaction that wrote these events has committed."""
        for msg in messages:
            for sub in list(self._subs):
                if sub.role is Role.TECH and sub.tech_id not in msg.techs:
                    continue
                try:
                    sub.queue.put_nowait(msg.body)
                except asyncio.QueueFull:
                    sub.overflowed = True  # the socket sees this and tells the view to reload


hub = Hub()
