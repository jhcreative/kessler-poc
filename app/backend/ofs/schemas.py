"""The API contract (RTS-2): written before the code that serves it (Pete).

Commands in, events out (plan §4). A view sends a `CommandIn`; the backend checks it against
`states.TRANSITIONS` and the rails, writes the job and one `job_events` row in one transaction, and
after the commit publishes an `EventEnvelope` on the WebSocket. Every envelope carries the
`job_events.id`, so a view that reconnects asks for everything after its last id (POC-05).

Money is integer cents everywhere. Times are UTC, ISO-8601.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from .states import ActorKind, State

Source = Literal["portal", "email", "facilit"]
Parts = Literal["none", "on_truck", "special_order"]
Extenuating = Literal[
    "access_denied",
    "after_hours",
    "return_visit",
    "scope_changed",
    "safety_hold",
    "parts_delay",
    "other",
]
DraftedBy = Literal["claude", "rules"]


class Actor(BaseModel):
    kind: ActorKind
    person_id: uuid.UUID | None = None
    label: str  # "Coordinator 1", "Simulator", "System"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- The JSON columns, typed. models.py validates each one on every write. ---


class CapRule(_Strict):
    kind: Literal["cap"]
    amount_cents: int
    text: str


class ReviewRule(_Strict):
    kind: Literal["review"]
    issue_type: str
    text: str


Rule = Annotated[CapRule | ReviewRule, Field(discriminator="kind")]
RULES = TypeAdapter(list[Rule])


class InvoiceLine(_Strict):
    desc: str
    cents: int


INVOICE_LINES = TypeAdapter(list[InvoiceLine])


# --- One payload per command: the event log is typed too. ---


class NoPayload(_Strict):
    pass


class DraftIntakePayload(_Strict):
    source: Source
    drafted_by: DraftedBy


class AssignPayload(_Strict):
    tech: str


class ClientApprovalPayload(_Strict):
    client_ref: str


class ReasonPayload(_Strict):
    reason: str


class ClosePayload(_Strict):
    actual_hours: float
    sign_off_by: str


class QbPayload(_Strict):
    qb_doc_number: str


PAYLOADS: dict[str, type[BaseModel]] = {
    "draft_intake": DraftIntakePayload,
    "qualify": NoPayload,
    "request_client_approval": NoPayload,
    "record_client_approval": ClientApprovalPayload,
    "approve_for_dispatch": NoPayload,
    "assign_tech": AssignPayload,
    "arrive": NoPayload,
    "set_needs_review": ReasonPayload,
    "reassign_tech": AssignPayload,
    "return_to_dispatch": NoPayload,
    "ask_to_wait": NoPayload,
    "close_job": ClosePayload,
    "draft_invoice": NoPayload,
    "approve_invoice": QbPayload,
    "send_back_invoice": ReasonPayload,
    "record_payment": QbPayload,
}


class Approval(_Strict):
    """Plan §5 C: who approved, when, and the client's own reference."""

    by: str
    at: datetime
    client_ref: str


class SignOff(_Strict):
    by: str  # the client rep, by role: "Store manager"
    at: datetime


class CommandIn(BaseModel):
    """POST /api/modules/fieldops/jobs/{job_id}/commands"""

    model_config = ConfigDict(extra="forbid")

    command: str
    # Optimistic concurrency: the job's `last_event_id` the view acted on. A stale one is refused
    # (409), so two people can't both move the same job from the same state.
    expected_event_id: int
    payload: dict[str, Any] = Field(default_factory=dict)
    # Plan §4: a person can override any rail but the three hard ones. The reason is recorded.
    override_reason: str | None = None


class EventEnvelope(BaseModel):
    """One `job_events` row, as every view receives it."""

    id: int
    job_id: uuid.UUID
    job_number: int
    at: datetime
    actor: Actor
    command: str
    from_state: State | None
    to_state: State
    payload: dict[str, Any]
    override_reason: str | None = None


class JobOut(BaseModel):
    """The one job record (plan §5), the same typed fields in every view."""

    id: uuid.UUID
    number: int
    # A: identity, set at intake, nobody edits it
    client_id: uuid.UUID
    client_name: str
    site_id: uuid.UUID
    site_label: str
    site_state: str
    client_wo: str
    client_po: str | None
    site_contact: str
    source: Source
    drafted_by: DraftedBy | None
    # B: working fields, two-way
    issue_type: str
    parts: Parts
    part_numbers: list[str]
    est_hours: float | None
    actual_hours: float | None
    extenuating: list[Extenuating]
    extenuating_note: str | None
    # C: approval
    requires_approval: bool
    rule_fired: str | None
    approval: Approval | None
    # D: state
    state: State
    queue: str
    owner_id: uuid.UUID | None
    tech_id: uuid.UUID | None
    window_start: datetime | None
    window_end: datetime | None
    sign_off: SignOff | None
    estimate_cents: int
    final_cents: int | None
    last_event_id: int
    updated_at: datetime


class Refusal(BaseModel):
    """A refused command: the 409 or 422 body. `reason` is a sentence a person can act on."""

    code: Literal["not_allowed", "stale", "role", "rail"]
    reason: str
