"""POC-07, C2: a request arrives and a job is drafted from it, by Claude or, labelled, by the rules."""

from __future__ import annotations

import random
import typing

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ofs import intake, sources
from ofs.intake import ClaudeDraft, Drafted, IntakeError, draft_job, rules_draft
from ofs.models import Client, Contract, Job, JobEvent, Site
from ofs.rules import evaluate
from ofs.seed import ISSUE_TYPES

from .helpers import sign_in

PREFIX = {
    "Bullseye": "BE-WO-",
    "Starbrew Coffee": "SB-",
    "Wellgreens Pharmacy": "WG-",
    "CVR Pharmacy": "CVR-",
    "Wegford Markets": "WF-",
    "Aldo Foods": "AF-",
    "Keystone Dental Group": "KD-",
    "Lehigh Valley Fitness": "LVF-",
}


async def _requests(session: AsyncSession, n: int, seed: int = 3) -> list[sources.Source]:
    rows = (await session.execute(select(Site, Client).join(Client, Client.id == Site.client_id))).all()
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        site, client = rng.choice(rows)
        ref = sources.SiteRef(
            client.name, client.channel, PREFIX[client.name], site.store_number, site.city, site.state, site.contact
        )
        out.append(sources.make(rng, ref))
    return out


def test_the_issue_types_agree_everywhere() -> None:
    assert set(typing.get_args(intake.IssueType)) == set(ISSUE_TYPES) == set(sources.ISSUE_PHRASES)


async def test_the_rules_read_every_shape_of_request(seeded: AsyncSession) -> None:
    """The fallback's own eval: 60 synthetic requests over every client and channel, every field exact."""
    clients = sorted((await seeded.execute(select(Client.name))).scalars())
    reqs = await _requests(seeded, 60)
    assert {r.channel for r in reqs} == {"portal", "email", "facilit"}
    for r in reqs:
        got = rules_draft(r.text, clients, "test").draft.model_dump()
        assert {k: got[k] or None for k in r.truth} == r.truth, r.text


def fake(draft: ClaudeDraft | None, tokens: tuple[int, int] = (900, 80)) -> intake.Drafter:
    async def drafter(text: str, clients: list[str]) -> Drafted:
        if draft is None:
            return rules_draft(text, clients, "Claude couldn't be reached")
        return Drafted(
            draft=draft, by="claude", model="claude-opus-5-5", input_tokens=tokens[0], output_tokens=tokens[1]
        )

    return drafter


async def test_a_claude_draft_becomes_a_job_with_its_cost_on_the_event(seeded: AsyncSession) -> None:
    r = (await _requests(seeded, 1, seed=11))[0]
    draft = ClaudeDraft.model_validate(r.truth)
    job, event = await draft_job(seeded, r.text, r.channel, intake.SIMULATOR, drafter=fake(draft))
    assert job.state == "intake_draft" and job.drafted_by == "claude" and job.source_text == r.text
    assert (job.client_wo, job.client_po, job.issue_type) == (
        r.truth["client_wo"],
        r.truth["client_po"],
        r.truth["issue_type"],
    )
    assert event.from_state is None and event.to_state == "intake_draft" and event.actor_label == "Simulator"
    assert event.payload == {
        "source": r.channel,
        "drafted_by": "claude",
        "model": "claude-opus-5-5",
        "input_tokens": 900,
        "output_tokens": 80,
    }
    contract = (await seeded.execute(select(Contract).where(Contract.client_id == job.client_id))).scalar_one()
    assert (job.requires_approval, job.rule_fired) == evaluate(contract.rules, job.issue_type, job.estimate_cents)
    assert job.last_event_id == event.id


async def test_when_claude_cant_the_rules_draft_it_and_say_why(seeded: AsyncSession) -> None:
    r = (await _requests(seeded, 1, seed=12))[0]
    job, event = await draft_job(seeded, r.text, r.channel, intake.SIMULATOR, drafter=fake(None))
    assert job.drafted_by == "rules" and event.payload["fallback_reason"] == "Claude couldn't be reached"
    assert job.client_wo == r.truth["client_wo"]


async def test_a_draft_naming_a_client_we_dont_have_goes_to_the_rules(seeded: AsyncSession) -> None:
    r = (await _requests(seeded, 1, seed=13))[0]
    wrong = ClaudeDraft.model_validate({**r.truth, "client_name": "Target"})
    job, event = await draft_job(seeded, r.text, r.channel, intake.SIMULATOR, drafter=fake(wrong))
    assert job.drafted_by == "rules" and "client or store we don't have" in event.payload["fallback_reason"]


async def test_no_key_and_the_daily_cap_both_fall_back_labelled(
    seeded: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = (await _requests(seeded, 1, seed=14))[0]
    _, event = await draft_job(seeded, r.text, r.channel, intake.SIMULATOR)
    assert event.payload["fallback_reason"] == "No Anthropic key is configured"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-used")
    monkeypatch.setattr(intake, "budget", intake._Budget(limit=0))
    _, event = await draft_job(seeded, r.text, r.channel, intake.SIMULATOR)
    assert "daily cap" in event.payload["fallback_reason"]


async def test_an_unreadable_request_drafts_nothing(seeded: AsyncSession) -> None:
    before = await seeded.scalar(select(func.count()).select_from(Job))
    with pytest.raises(IntakeError):
        await draft_job(seeded, "Hello, something is broken somewhere.", "email", intake.SIMULATOR)
    assert await seeded.scalar(select(func.count()).select_from(Job)) == before


async def test_the_coordinator_sends_in_a_request_and_it_lands_in_drafts(
    logins: AsyncSession, client: httpx.AsyncClient
) -> None:
    await sign_in(client, "coord@kfs.com")
    r = await client.post("/api/intake/simulate")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job"]["state"] == "intake_draft" and body["job"]["drafted_by"] == "rules"
    assert body["events"][0]["actor"]["label"] == "Simulator"
    contract = (await client.get(f"/api/jobs/{body['job']['id']}/contract")).json()
    assert contract["client_name"] == body["job"]["client_name"] and contract["rules"][0]["kind"] == "cap"
    await sign_in(client, "dispatch@kfs.com")
    assert (await client.post("/api/intake/simulate")).status_code == 403
    assert await logins.scalar(select(func.count()).select_from(JobEvent).where(JobEvent.command == "draft_intake"))
