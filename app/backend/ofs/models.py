"""The data model (plan §5): one job record and everything it checks against.

Money is integer cents. Times are timezone-aware UTC. Every enumerated column has a CHECK, so the
database refuses a value the code would.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, validates

from . import schemas
from .db import Base
from .states import ActorKind, Role, State

STATES_SEVEN = ("PA", "OH", "NY", "NJ", "DE", "WV", "MD")


def _in(column: str, values: tuple[str, ...] | list[str], name: str) -> CheckConstraint:
    listed = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({listed})", name=name)


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Client(Base):
    """Fictional but recognizable; FacilIT is a real product, used here as a channel (plan §7)."""

    __tablename__ = "clients"
    __table_args__ = (_in("channel", ("portal", "email", "facilit"), "ck_clients_channel"),)

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(120), unique=True)
    channel: Mapped[str] = mapped_column(String(16))
    invoice_format: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = _now()


class Contract(Base):
    """Read-only to the job (page 2: checked before work is assigned)."""

    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = _pk()
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), unique=True)
    issue_types: Mapped[list[str]] = mapped_column(JSONB)
    # [{"kind": "cap", "amount_cents": 2500000, "text": "..."},
    #  {"kind": "review", "issue_type": "hvac", "text": "..."}]
    rules: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)  # list[schemas.Rule]
    net_days: Mapped[int] = mapped_column(Integer)

    @validates("rules")
    def _rules(self, _key: str, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rules: list[dict[str, Any]] = schemas.RULES.dump_python(schemas.RULES.validate_python(value), mode="json")
        return rules


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (_in("state", STATES_SEVEN, "ck_sites_state"),)

    id: Mapped[uuid.UUID] = _pk()
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), index=True)
    store_number: Mapped[str] = mapped_column(String(16))
    label: Mapped[str] = mapped_column(String(160))
    address: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(2))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    contact: Mapped[str] = mapped_column(String(120))


class Person(Base):
    """Role names only (plan §7). The five demo logins carry an email; auth lands in POC-04."""

    __tablename__ = "people"
    __table_args__ = (_in("role", [r.value for r in Role], "ck_people_role"),)

    id: Mapped[uuid.UUID] = _pk()
    label: Mapped[str] = mapped_column(String(60), unique=True)
    role: Mapped[str] = mapped_column(String(16))
    email: Mapped[str | None] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(80))


class Tech(Base):
    __tablename__ = "techs"

    id: Mapped[uuid.UUID] = _pk()
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id"), unique=True)
    skills: Mapped[list[str]] = mapped_column(JSONB)
    licenses: Mapped[list[str]] = mapped_column(JSONB)  # states the tech is licensed in
    home_city: Mapped[str] = mapped_column(String(80))
    home_lat: Mapped[float] = mapped_column(Float)
    home_lng: Mapped[float] = mapped_column(Float)
    truck: Mapped[str] = mapped_column(String(8), unique=True)


class FleetPosition(Base):
    """Simulated Samsara: one current position per truck."""

    __tablename__ = "fleet_positions"
    __table_args__ = (_in("status", ("parked", "driving", "onsite"), "ck_fleet_status"),)

    truck: Mapped[str] = mapped_column(ForeignKey("techs.truck"), primary_key=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(8))


class Job(Base):
    """The one job record. A: identity. B: working fields. C: approval. D: state."""

    __tablename__ = "jobs"
    __table_args__ = (
        _in("source", ("portal", "email", "facilit"), "ck_jobs_source"),
        _in("parts", ("none", "on_truck", "special_order"), "ck_jobs_parts"),
        _in("state", [s.value for s in State], "ck_jobs_state"),
        CheckConstraint("drafted_by IS NULL OR drafted_by IN ('claude', 'rules')", name="ck_jobs_drafted_by"),
        CheckConstraint("estimate_cents >= 0", name="ck_jobs_estimate"),
        Index("ix_jobs_state", "state"),
    )

    id: Mapped[uuid.UUID] = _pk()
    number: Mapped[int] = mapped_column(Integer, Identity(start=1001), unique=True)
    # A: identity
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"))
    client_wo: Mapped[str] = mapped_column(String(40))
    client_po: Mapped[str | None] = mapped_column(String(40))
    site_contact: Mapped[str] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(16))
    source_text: Mapped[str] = mapped_column(Text)
    drafted_by: Mapped[str | None] = mapped_column(String(8))
    # B: working fields
    issue_type: Mapped[str] = mapped_column(String(32))
    parts: Mapped[str] = mapped_column(String(16), default="none")
    part_numbers: Mapped[list[str]] = mapped_column(JSONB, default=list)
    est_hours: Mapped[float | None] = mapped_column(Float)
    actual_hours: Mapped[float | None] = mapped_column(Float)
    extenuating: Mapped[list[str]] = mapped_column(JSONB, default=list)
    extenuating_note: Mapped[str | None] = mapped_column(String(200))
    # C: approval
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    rule_fired: Mapped[str | None] = mapped_column(String(300))
    approval: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # D: state
    state: Mapped[str] = mapped_column(String(24))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("people.id"))
    tech_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("techs.id"))
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sign_off: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    estimate_cents: Mapped[int] = mapped_column(Integer)
    final_cents: Mapped[int | None] = mapped_column(Integer)
    last_event_id: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    @validates("approval")
    def _approval(self, _key: str, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else schemas.Approval.model_validate(value).model_dump(mode="json")

    @validates("sign_off")
    def _sign_off(self, _key: str, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else schemas.SignOff.model_validate(value).model_dump(mode="json")


class JobEvent(Base):
    """Append-only history. Feeds the WebSocket, the replay, and turnaround per step."""

    __tablename__ = "job_events"
    __table_args__ = (
        _in("actor_kind", [k.value for k in ActorKind], "ck_job_events_actor_kind"),
        Index("ix_job_events_job", "job_id", "id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_kind: Mapped[str] = mapped_column(String(16))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("people.id"))
    actor_label: Mapped[str] = mapped_column(String(60))
    command: Mapped[str] = mapped_column(String(40))
    from_state: Mapped[str | None] = mapped_column(String(24))
    to_state: Mapped[str] = mapped_column(String(24))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    override_reason: Mapped[str | None] = mapped_column(String(300))

    def __init__(self, **kw: Any) -> None:
        """The payload is checked against its command's model before the row exists (schemas.PAYLOADS)."""
        model = schemas.PAYLOADS.get(kw.get("command", ""))
        if model is None:
            raise ValueError(f"unknown command {kw.get('command')!r}")
        kw["payload"] = model.model_validate(kw.get("payload") or {}).model_dump(mode="json")
        super().__init__(**kw)


class Invoice(Base):
    """Drafted at close, in the client's format."""

    __tablename__ = "invoices"
    __table_args__ = (_in("state", ("draft", "submitted", "sent_back"), "ck_invoices_state"),)

    id: Mapped[uuid.UUID] = _pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), unique=True)
    lines: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    total_cents: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16))
    check_passed: Mapped[bool] = mapped_column(Boolean)
    check_note: Mapped[str | None] = mapped_column(String(300))
    qb_doc_number: Mapped[str | None] = mapped_column(String(16), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @validates("lines")
    def _lines(self, _key: str, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lines = schemas.INVOICE_LINES.validate_python(value)
        dumped: list[dict[str, Any]] = schemas.INVOICE_LINES.dump_python(lines, mode="json")
        return dumped


class QbLedger(Base):
    """QuickBooks (simulated). Aging is computed from it."""

    __tablename__ = "qb_ledger"

    id: Mapped[uuid.UUID] = _pk()
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("invoices.id"), unique=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    doc_number: Mapped[str] = mapped_column(String(16), unique=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
