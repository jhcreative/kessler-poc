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
    """Who drafted the job from its source, and what it cost (plan §7: tokens logged on the event)."""

    source: Source
    drafted_by: DraftedBy
    model: str | None = None  # the model that served the draft, when Claude did
    input_tokens: int | None = None
    output_tokens: int | None = None
    fallback_reason: str | None = None  # why the rules drafted it instead of Claude


class AssignPayload(_Strict):
    tech: str  # the tech's label, "Tech 4"
    window_start: datetime | None = None  # default: an hour from now, two hours long


class ClientApprovalPayload(_Strict):
    by: str  # by role: "Client facilities manager"
    client_ref: str


class ReasonPayload(_Strict):
    reason: str


class ClosePayload(_Strict):
    """Plan §4: no close without a sign-off or a reason."""

    actual_hours: float
    sign_off_by: str | None = None
    no_sign_off_reason: str | None = None


class FieldsIn(_Strict):
    """Part B, the working fields: two-way, office and field. Part A (identity) is never editable."""

    issue_type: str | None = None
    parts: Parts | None = None
    part_numbers: list[str] | None = None
    est_hours: float | None = None
    actual_hours: float | None = None
    extenuating: list[Extenuating] | None = None
    extenuating_note: str | None = None
    estimate_cents: int | None = Field(default=None, ge=0)  # the coordinator's, not the tech's


class FieldsChanged(_Strict):
    changes: FieldsIn


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
    "update_fields": FieldsChanged,
}

# What a person sends, where it differs from what the event records.
REQUESTS: dict[str, type[BaseModel]] = {
    **PAYLOADS,
    "approve_invoice": NoPayload,  # QuickBooks (simulated) assigns the doc number
    "update_fields": FieldsIn,
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
    source_text: str  # the request as it arrived: the coordinator checks the draft against it (C2)
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
    owner_label: str | None
    tech_id: uuid.UUID | None
    tech_label: str | None
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


class CommandResult(BaseModel):
    """What a command returns: the job as it now is, and the events it wrote (two at close: the invoice is drafted)."""

    job: JobOut
    events: list[EventEnvelope]


class StepTurnaround(BaseModel):
    """Time spent in one state (Q9): how long jobs waited there, from `job_events`. The waits are the Cost of Delay."""

    state: State
    queue: str
    open: int  # jobs in this state now
    open_hours_avg: float | None  # how long they've been waiting
    done: int  # times a job has left this state
    done_hours_median: float | None  # how long it usually takes to leave


class Overview(BaseModel):
    total: int
    steps: list[StepTurnaround]  # in state-machine order
    as_of: datetime


# --- The WebSocket's frames (ws.py). Not in FastAPI's OpenAPI, so tools/export_openapi.py adds them. ---


class LiveHello(BaseModel):
    type: Literal["hello"] = "hello"
    last_event_id: int


class LiveEvent(BaseModel):
    type: Literal["event"] = "event"
    event: EventEnvelope
    job: JobOut


class LivePing(BaseModel):
    type: Literal["ping"] = "ping"


class LiveResync(BaseModel):
    type: Literal["resync"] = "resync"


LiveMessage = Annotated[LiveHello | LiveEvent | LivePing | LiveResync, Field(discriminator="type")]
LIVE_MESSAGE: TypeAdapter[LiveHello | LiveEvent | LivePing | LiveResync] = TypeAdapter(LiveMessage)


class ContractOut(BaseModel):
    """The contract panel: read-only to the job (page 2: checked before work is assigned)."""

    client_name: str
    channel: Source
    invoice_format: str
    issue_types: list[str]
    rules: list[Rule]
    net_days: int


class CandidateOut(BaseModel):
    tech_id: uuid.UUID
    label: str
    truck: str
    eligible: bool
    distance_km: float
    load: int
    score: float | None
    reasons: list[str]
    gaps: list[str]


class Recommendation(BaseModel):
    """D2: every tech, the eligible ones first by score. `top` is the recommendation, or null if nobody qualifies."""

    job_id: uuid.UUID
    top: CandidateOut | None
    candidates: list[CandidateOut]


class TechOut(BaseModel):
    id: uuid.UUID
    label: str
    skills: list[str]
    licenses: list[str]
    home_city: str
    truck: str
    truck_status: Literal["parked", "driving", "onsite"]
    lat: float
    lng: float
    load: int  # jobs on their board: assigned, onsite or needs review
