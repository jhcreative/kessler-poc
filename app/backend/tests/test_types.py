"""The JSON columns are typed: a malformed value is refused before it reaches the database."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ofs.models import Contract, Invoice, Job, JobEvent
from ofs.schemas import PAYLOADS
from ofs.states import TRANSITIONS, UPDATE_FIELDS


def test_every_command_has_a_payload_model() -> None:
    assert set(PAYLOADS) == set(TRANSITIONS) | {UPDATE_FIELDS}


def test_event_payload_must_match_its_command() -> None:
    kw = {
        "job_id": uuid.uuid4(),
        "at": datetime.now(UTC),
        "actor_kind": "person",
        "actor_label": "Dispatcher",
        "from_state": "ready_for_dispatch",
        "to_state": "assigned",
    }
    assert JobEvent(command="assign_tech", payload={"tech": "Tech 4"}, **kw).payload == {"tech": "Tech 4"}
    with pytest.raises(ValidationError):
        JobEvent(command="assign_tech", payload={"technician": "Tech 4"}, **kw)
    with pytest.raises(ValueError, match="unknown command"):
        JobEvent(command="teleport", payload={}, **kw)


def test_rules_lines_approval_and_sign_off_are_checked() -> None:
    with pytest.raises(ValidationError):
        Contract(rules=[{"kind": "cap", "amount": 100, "text": "x"}])
    with pytest.raises(ValidationError):
        Invoice(lines=[{"desc": "Labor", "cents": "lots"}])
    with pytest.raises(ValidationError):
        Job(approval={"by": "Client", "client_ref": "APR-1"})  # no time: not evidence
    job = Job(sign_off={"by": "Store manager", "at": "2026-11-16T09:00:00Z"})
    assert job.sign_off == {"by": "Store manager", "at": "2026-11-16T09:00:00Z"}
