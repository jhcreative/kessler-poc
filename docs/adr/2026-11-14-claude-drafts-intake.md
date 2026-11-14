# 2026-11-14: Claude drafts intake, the rules stand behind it

## Status
Accepted (John, Q3, 2026-11-14). The model was chosen at build time, as the plan said it would be (plan §7).

## Context
Page 3's first gear is "draft from source": a request arrives through a portal, an email or FacilIT, and someone
re-keys it today. The POC drafts the job from the request, and the coordinator checks the draft before anything moves
(C2). A drafting call can fail, be refused, or have no key, and the demo must never stall.

## Decision
- **Claude drafts.** Model `claude-opus-5-5`, the default of the `claude-api` skill loaded before the code was written.
  Effort is `low`, because this is an extraction and not reasoning. The output is structured into a Pydantic model
  (`ClaudeDraft`) and validated by the SDK, with server-side refusal fallbacks on. SDK `anthropic==2.3.0`.
- **The rules draft when Claude can't.** That covers no key, the daily cap, a failed call, a refusal, and a draft
  naming a client or store we don't have. The job and its event say so, with the reason.
- **Labelled everywhere.** "Drafted by Claude from source", or "Drafted by the rules from source", with the model and
  tokens on the job's event.
- **Cost controls:** an in-app daily cap (`OFS_CLAUDE_DAILY_LIMIT`, 300) on top of the account's spend cap and alert
  (John's).
- **Privacy:** only the synthetic request text is sent. The key lives in `~/jhc/secrets/anthropic.env` and reaches the
  container at runtime.

## Consequences
- Measured on two live calls: both drafts exact; about 1,000 tokens in and 80 out; 2 to 3.5 s. At $4 and $20 per
  million tokens, that's about half a cent a draft, roughly $0.45 for an hour of demo at one request every 45 s.
- The gate never calls the model. The Claude path is tested against a fake, and the rules against 60 synthetic
  requests in every shape.
- **A different model is one line** (`MODEL` in `ofs/intake.py`). The plan's first thought was a Sonnet-class model;
  the skill's rule is Opus 5.5 unless John names another. At this volume, the cost difference is cents.

## Positions
**John (product owner), Q3:** "yes lets go for it".

**Plan §7 (the team, approved by John):** "the build loads the `claude-api` skill first and picks the current model
then. A Sonnet-class model is the default for extraction, and the choice is recorded."

**Cesar (technical director), at build time:** the skill's default is `claude-opus-5-5` unless the product owner names
another, so Opus 5.5 at low effort. Switching to Sonnet is one line if John prefers it.

## Participants
John (decision); Cesar, Pete, Jen, Orly; Anne (record).
