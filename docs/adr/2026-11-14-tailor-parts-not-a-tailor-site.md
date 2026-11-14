# 2026-11-14: Tailor's parts, not a Tailor site

## Status
Accepted (John, 2026-11-14). It amends plan §8 and §9 and supersedes POC-02's first build.

## Context
POC-02 scaffolded a full Tailor instance and mounted the `fieldops` module in it. It worked, and the measurement after
it settled the question: the POC was 369 lines inside an instance of 1,441 files and about 117,000 lines. That's
44,000 lines of backend and 72,000 of frontend, for pages, blocks, media, the workbench, alterations, feeds, search
and the AEO artifacts. The app also had to meet publishing contracts it has no use for: Path P export hooks and a
backend suite of 2,500 tests that takes 98 seconds. And the repo is a deliverable. A reader at Jahnel would have found
a CMS with a small module inside it, which is the "new master system" story the message argues against (CLAUDE.md).

## Decision
The app is its own small codebase in this repo, under `app/`. It is built from Tailor's parts, not as a Tailor site:

| From Tailor | How |
|---|---|
| FastAPI, SQLAlchemy 2 (async), Alembic, Postgres, Pydantic | The same pinned versions as Tailor v1.1.5's lockfile |
| The session rule (ADR-0102) | A request's session commits and closes before its response |
| Auth | The session-cookie pattern and bcrypt, cut down to the five demo roles (POC-04) |
| The frontend shell | React Router 7, the house tokens and fonts, hand-rolled components; AG Grid Community for grids (POC-06) |
| Run and deploy | Docker Compose and Caddy; `IMAGES=local` (build here, `docker save \| ssh docker load`) behind the box's edge Caddy |
| Types | Typed end to end. Pydantic is the one source (enums, the API, every JSON column, one payload model per command); the TypeScript models are generated from its OpenAPI, and the gate fails on drift (John, 2026-11-14: "we will want them to correspond to Typescript models for front end", "i know its our usual but want to reinforce here") |

Nothing that publishes ports over: no pages, blocks, media library, workbench, SEO, AEO, feeds or alterations.

**The shape (John):** admin is only users, integrations and config. The work happens in the frontend, one view per
role: coordinator, dispatch, tech, controller, and the overview.

## Consequences
### Positive
- The repo is the POC: every file in `app/` is about the job record.
- The gate runs in seconds, against Postgres rather than SQLite, so CHECK constraints and transactions are real.
- No publishing contract shapes the data model.

### Negative
- POC-02's instance-module seam is retired unused (`~/jhc/sites/jahnel-poc`, kept as the record of it, its stack
  stopped).
- The deploy loses Tailor's `deploy-box.sh` (1,982 lines, built for content sites: backups, the write check, the TLS
  carry). Rob writes a short ship script for this app on the same edge-mode pattern. R1 (the first WebSocket through
  edge Caddy) is unchanged.
- Auth is ours to cut down correctly. Orly reviews it at POC-04 (RTS-6).

## Positions
**John (product owner):** "oh - i thought we'd just use parts of Tailor - do we really think its suited ot framerwork
for app like this?" Then: "I mean the whole publihsing thing is crift", "we dont publihs pages, we handle data", "we
dont care about AEO/SEo", "etc". And: "yeah 'admin' for this would be just users/integrations/config. the
frontend is where work gets done for eaxch role".

**Cesar (technical director):** "Agreed. Tailor is a publishing platform. It gives this app its plumbing at the price
of 117,000 lines it never runs, and the repo is something Jahnel reads. Take the parts: the stack, the session rule,
the auth pattern, the shell, the deploy pattern."

**Angela (product owner, the team's PO):** "The plan said 'Tailor pieces'. The handoff turned that into a scaffold. This
puts it back to what we approved."

## Participants
John (decision); Cesar, Angela, Pete, Orly; Anne (record).
