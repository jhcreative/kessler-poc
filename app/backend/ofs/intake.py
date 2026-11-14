"""Intake: a request arrives, and a job is drafted from it (C2, page 3's "draft from source" gear).

Claude drafts first: structured output into `ClaudeDraft`, validated by the SDK. The rules draft instead, labelled as
such on the job and on its event, whenever Claude can't: no key, the daily cap reached, the call failed, the model
declined, or the draft named a client or store we don't have. The demo never stalls (plan §7).

Model and settings (the `claude-api` skill, loaded 2026-11-14): `claude-opus-5-5`, the skill's default, at effort
`low` (an extraction, not reasoning), with server-side refusal fallbacks on (`fallbacks: "default"`). The key is
read from the environment (`ANTHROPIC_API_KEY`, from `~/jhc/secrets/anthropic.env`), never from the repo. Only the
synthetic request text is sent, and each call's tokens are logged on the job's event, not the prompt.

Cost controls (Cesar): a daily call cap in the app (`OFS_CLAUDE_DAILY_LIMIT`, default 300), on top of the spend cap
and alert John sets on the account.
"""

from __future__ import annotations

import os
import re
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Literal, Protocol

import anthropic
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .commands import Actor, _record
from .models import Client, Contract, Job, Site
from .rules import evaluate
from .sources import ISSUE_PHRASES
from .states import ActorKind, State

MODEL = "claude-opus-5-5"
IssueType = Literal["hvac", "refrigeration", "electrical", "plumbing", "doors_locks", "lighting", "roofing", "general"]


class ClaudeDraft(BaseModel):
    """What Claude extracts from a request. Identity (part A) plus the issue type; nothing is invented."""

    client_name: str = Field(description="The client exactly as named in the list of known clients")
    store_number: str = Field(description="The store or location number, digits only")
    client_wo: str = Field(description="The client's work order or reference number, exactly as written")
    client_po: str | None = Field(description="The purchase order number if one is given, else null")
    site_contact: str = Field(description="Who to contact at the site, with their phone number, as written")
    issue_type: IssueType = Field(description="The trade the problem belongs to")


@dataclass
class Drafted:
    draft: ClaudeDraft
    by: Literal["claude", "rules"]
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    fallback_reason: str | None = None


class Drafter(Protocol):
    async def __call__(self, text: str, clients: list[str]) -> Drafted: ...


# --- Claude ---

SYSTEM = (
    "You draft facilities work orders for OneFamilyServices from requests as they arrive: client portal records, "
    "store emails and FacilIT tickets. Extract only what the request says. Use the client's name exactly as it "
    "appears in the list of known clients. If a field isn't in the request, say so with null where the schema allows "
    "it; never guess a number."
)


@dataclass
class _Budget:
    limit: int
    day: date = field(default_factory=lambda: datetime.now(UTC).date())
    used: int = 0

    def take(self) -> bool:
        today = datetime.now(UTC).date()
        if today != self.day:
            self.day, self.used = today, 0
        if self.used >= self.limit:
            return False
        self.used += 1
        return True


budget = _Budget(limit=int(os.environ.get("OFS_CLAUDE_DAILY_LIMIT", "300")))
_client: anthropic.AsyncAnthropic | None = None


def _claude() -> anthropic.AsyncAnthropic | None:
    global _client
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    if _client is None:
        _client = anthropic.AsyncAnthropic(timeout=30.0, max_retries=1)
    return _client


async def claude_drafter(text: str, clients: list[str]) -> Drafted:
    client = _claude()
    if client is None:
        return rules_draft(text, clients, "No Anthropic key is configured")
    if not budget.take():
        return rules_draft(text, clients, f"The daily cap of {budget.limit} Claude drafts is reached")
    try:
        response = await client.beta.messages.parse(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Known clients: {', '.join(clients)}.\n\nThe request:\n<request>\n{text}\n</request>",
                }
            ],
            output_format=ClaudeDraft,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError:
        return rules_draft(text, clients, "Claude couldn't be reached")
    except anthropic.RateLimitError:
        return rules_draft(text, clients, "Claude is rate limited")
    except anthropic.APIStatusError as exc:
        return rules_draft(text, clients, f"Claude answered {exc.status_code}")
    if response.stop_reason == "refusal" or response.parsed_output is None:
        return rules_draft(text, clients, f"Claude didn't draft it ({response.stop_reason})")
    return Drafted(
        draft=response.parsed_output,
        by="claude",
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


# --- The rules: always available, and labelled as such ---

_WO = re.compile(r"\b(?:Work order|Ref|reference number is)\W+([A-Z]{2,4}-(?:WO-)?\d{6})", re.I)
_PO = re.compile(r"\bPO-\d{5}\b")
_STORE = re.compile(r"#(\d{3,5})")
_CONTACT = re.compile(r"(Store manager, \(555\) \d{4})")
_PHONE = re.compile(r"\(555\) \d{4}")


def rules_draft(text: str, clients: list[str], reason: str) -> Drafted:
    client = next((c for c in sorted(clients, key=len, reverse=True) if c.lower() in text.lower()), "")
    store = _STORE.search(text)
    wo = _WO.search(text)
    po = _PO.search(text)
    contact = _CONTACT.search(text)
    phone = _PHONE.search(text)
    issue: str = "general"
    for kind, phrases in ISSUE_PHRASES.items():
        if any(p.lower() in text.lower() for p in phrases) or kind.replace("_", " / ") in text.lower():
            issue = kind
            break
    draft = ClaudeDraft(
        client_name=client,
        store_number=store.group(1) if store else "",
        client_wo=wo.group(1) if wo else "",
        client_po=po.group(0) if po else None,
        site_contact=contact.group(1).strip() if contact else (f"Store manager, {phone.group(0)}" if phone else ""),
        issue_type=issue,  # type: ignore[arg-type]
    )
    return Drafted(draft=draft, by="rules", fallback_reason=reason)


# --- From a request to a job ---


class IntakeError(Exception):
    """The request names no client and store we can match, even by the rules. Nothing is created."""


async def _like_jobs(session: AsyncSession, client_id: uuid.UUID, issue: str) -> tuple[int, float | None]:
    """The estimate and hours from like jobs: same client and issue, else same issue (plan §5 B)."""
    for where in ((Job.client_id == client_id, Job.issue_type == issue), (Job.issue_type == issue,)):
        rows = (await session.execute(select(Job.estimate_cents, Job.est_hours).where(*where))).all()
        if rows:
            hours = [h for _, h in rows if h is not None]
            return int(statistics.median(c for c, _ in rows)), (round(statistics.median(hours), 1) if hours else None)
    return 500_000, None


async def draft_job(
    session: AsyncSession,
    text: str,
    channel: str,
    actor: Actor,
    drafter: Drafter = claude_drafter,
    now: datetime | None = None,
) -> tuple[Job, Any]:
    """Draft a job from a request, in the caller's transaction. Returns the job and its `draft_intake` event."""
    now = now or datetime.now(UTC)
    clients = {c.name: c for c in (await session.execute(select(Client))).scalars()}
    result = await drafter(text, sorted(clients))
    site = await _site(session, clients, result.draft) if result.draft.client_name in clients else None
    if site is None and result.by == "claude":  # Claude named something we don't have: the rules try instead
        result = rules_draft(text, sorted(clients), "Claude's draft named a client or store we don't have")
        site = await _site(session, clients, result.draft) if result.draft.client_name in clients else None
    if site is None:
        raise IntakeError("The request names no client and store we can match. Nothing was drafted")

    d = result.draft
    contract = (await session.execute(select(Contract).where(Contract.client_id == site.client_id))).scalar_one()
    issue = d.issue_type if d.issue_type in contract.issue_types else "general"
    estimate, est_hours = await _like_jobs(session, site.client_id, issue)
    requires, rule = evaluate(contract.rules, issue, estimate)
    job = Job(
        client_id=site.client_id,
        site_id=site.id,
        client_wo=d.client_wo or "(not in the request)",
        client_po=d.client_po,
        site_contact=d.site_contact or site.contact,
        source=channel,
        source_text=text,
        drafted_by=result.by,
        issue_type=issue,
        parts="none",
        part_numbers=[],
        est_hours=est_hours,
        extenuating=[],
        requires_approval=requires,
        rule_fired=rule,
        state=State.INTAKE_DRAFT.value,
        estimate_cents=estimate,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    await session.flush()
    payload = {
        "source": channel,
        "drafted_by": result.by,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "fallback_reason": result.fallback_reason,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    event = await _record(session, job, "draft_intake", None, State.INTAKE_DRAFT, actor, payload, None, now)
    return job, event


async def _site(session: AsyncSession, clients: dict[str, Client], d: ClaudeDraft) -> Site | None:
    client = clients[d.client_name]
    return await session.scalar(
        select(Site).where(Site.client_id == client.id, Site.store_number == d.store_number.lstrip("#"))
    )


SIMULATOR = Actor(ActorKind.SIMULATOR)
