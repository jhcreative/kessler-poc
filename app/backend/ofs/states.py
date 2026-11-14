"""The job's states and the commands that move it: the one table the backend, the seed and the tests share.

Plan §5, left to right:

  intake_draft → qualified → (needs_client_approval ↔ qualified) → ready_for_dispatch → assigned
  → onsite → (needs_review → assigned / ready_for_dispatch / onsite) → closed → billing_review
  → invoiced → paid

A view never writes another view's state: it sends a command (plan §4). POC-04 enforces this table
and the rails; POC-03's seed walks it, so every seeded history is one the backend would allow.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class State(StrEnum):
    INTAKE_DRAFT = "intake_draft"
    QUALIFIED = "qualified"
    NEEDS_CLIENT_APPROVAL = "needs_client_approval"
    READY_FOR_DISPATCH = "ready_for_dispatch"
    ASSIGNED = "assigned"
    ONSITE = "onsite"
    NEEDS_REVIEW = "needs_review"
    CLOSED = "closed"
    BILLING_REVIEW = "billing_review"
    INVOICED = "invoiced"
    PAID = "paid"


class Role(StrEnum):
    """Ops roles (the module's `people` table). Core's role tiers are untouched (plan §8)."""

    COORDINATOR = "coordinator"
    DISPATCHER = "dispatcher"
    TECH = "tech"
    CONTROLLER = "controller"
    EXEC = "exec"  # reads the overview; issues no command


class ActorKind(StrEnum):
    PERSON = "person"
    SIMULATOR = "simulator"  # labelled as such in every view (G2)
    SYSTEM = "system"  # the backend's own step, e.g. drafting the invoice at close


@dataclass(frozen=True)
class Transition:
    command: str
    sources: frozenset[State | None]
    target: State
    roles: frozenset[Role]  # who may issue it; empty = system or simulator only


def _t(command: str, sources: set[State | None], target: State, *roles: Role) -> Transition:
    return Transition(command, frozenset(sources), target, frozenset(roles))


S, R = State, Role

TRANSITIONS: dict[str, Transition] = {
    t.command: t
    for t in (
        _t("draft_intake", {None}, S.INTAKE_DRAFT),
        _t("qualify", {S.INTAKE_DRAFT}, S.QUALIFIED, R.COORDINATOR),
        _t("request_client_approval", {S.QUALIFIED}, S.NEEDS_CLIENT_APPROVAL, R.COORDINATOR),
        _t("record_client_approval", {S.NEEDS_CLIENT_APPROVAL}, S.QUALIFIED, R.COORDINATOR),
        _t("approve_for_dispatch", {S.QUALIFIED}, S.READY_FOR_DISPATCH, R.COORDINATOR),
        _t("assign_tech", {S.READY_FOR_DISPATCH}, S.ASSIGNED, R.DISPATCHER),
        _t("arrive", {S.ASSIGNED}, S.ONSITE, R.TECH),
        _t("set_needs_review", {S.ASSIGNED, S.ONSITE}, S.NEEDS_REVIEW, R.TECH),
        _t("reassign_tech", {S.NEEDS_REVIEW}, S.ASSIGNED, R.DISPATCHER, R.COORDINATOR),
        _t(
            "return_to_dispatch",
            {S.NEEDS_REVIEW},
            S.READY_FOR_DISPATCH,
            R.DISPATCHER,
            R.COORDINATOR,
        ),
        _t("ask_to_wait", {S.NEEDS_REVIEW}, S.ONSITE, R.DISPATCHER, R.COORDINATOR),
        _t("close_job", {S.ONSITE}, S.CLOSED, R.TECH),
        _t("draft_invoice", {S.CLOSED}, S.BILLING_REVIEW),
        _t("approve_invoice", {S.BILLING_REVIEW}, S.INVOICED, R.CONTROLLER),
        _t("send_back_invoice", {S.BILLING_REVIEW}, S.CLOSED, R.CONTROLLER),
        _t("record_payment", {S.INVOICED}, S.PAID),
    )
}

# The happy path, one command per step (plan §11: happy path first).
HAPPY_PATH: tuple[str, ...] = (
    "draft_intake",
    "qualify",
    "approve_for_dispatch",
    "assign_tech",
    "arrive",
    "close_job",
    "draft_invoice",
    "approve_invoice",
    "record_payment",
)

# The page-2 queue each state sits in, for the overview (G3).
QUEUE: dict[State, str] = {
    S.INTAKE_DRAFT: "coordinator",
    S.QUALIFIED: "coordinator",
    S.NEEDS_CLIENT_APPROVAL: "coordinator",
    S.READY_FOR_DISPATCH: "dispatch",
    S.ASSIGNED: "field",
    S.ONSITE: "field",
    S.NEEDS_REVIEW: "dispatch",
    S.CLOSED: "billing",
    S.BILLING_REVIEW: "billing",
    S.INVOICED: "collections",
    S.PAID: "done",
}


def allowed(command: str, source: State | None) -> bool:
    t = TRANSITIONS.get(command)
    return t is not None and source in t.sources
