# Tailor's parts, not a Tailor site (11:00 to 11:30)

## The moment

POC-03 had started, schemas first, when John asked: "oh - i thought we'd just use parts of Tailor - do we really think
its suited ot framerwork for app like this?" Then, in quick succession: "I mean the whole publihsing thing is crift",
"we dont publihs pages, we handle data", "we dont care about AEO/SEo", "etc", and "yeah 'admin' for this would be just
users/integrations/config. the frontend is where work gets done for eaxch role". (His words, verbatim: ST-10.)

## What the measurement said

Cesar measured before answering. The POC was **369 lines** inside an instance of **1,441 files and about 117,000
lines** (44,000 backend, 72,000 frontend) of publishing platform: pages, blocks, media, the workbench, alterations,
feeds, search, SEO and AEO. Its backend suite took 98 seconds and imposed publishing contracts the POC never used.

The repo is also a deliverable, and a reader at Jahnel would have found a CMS with a small module inside it. That's
the "new master system" story the whole engagement argues against.

## The decision

The app became its own small codebase in this repo, under `app/`, built from Tailor's parts:
- FastAPI, SQLAlchemy 2, Alembic, Postgres and Pydantic, at Tailor's own pinned versions;
- Tailor's session rule (commit before the response);
- its cookie-auth pattern and bcrypt;
- the React Router 7 shell with the house tokens and fonts;
- AG Grid Community for grids;
- Docker Compose, Caddy, and the `IMAGES=local` deploy pattern.

Nothing that publishes came over.

**Recorded in:** `docs/adr/2026-11-14-tailor-parts-not-a-tailor-site.md`, with John's words, Cesar's and Angela's
positions, and the measurements.

## It became the agency's pattern

John: "Anne Cesar save this pattern as future base for liek apps", then "that are not Tailor web/ecom/blog but actual
apps liek this POC". Then, on types: "we will want them to correspond to Typescript models for front end" and "i know
its our usual but want to reinforce here". And on the stack: "we shoudl eb able to do this same thing all in javacript
with Node backend", "as a team on future project without much extra direction".

**Recorded in:**
- **Agency ADR-0014** (`jhc-agency/docs/adr/ADR-0014-data-apps-from-tailor-parts.md`): websites, shops and blogs stay
  Tailor sites; actual apps use this base. Typed end to end. The same base in Node: Fastify, Drizzle, zod, `ws`,
  vitest.
- **TEAM-11** (`jhc-agency/docs/backlog/TEAM-11-data-app-base.md`): extract the template from this app after Monday.
  It's done when an agent given only the skill and a short brief builds a two-role app on each stack.
- **The team memory**, so every future session starts with it.

## What it cost, and what it saved

- **Cost:** under 30 minutes from the question to the lean skeleton committed with POC-03 (`dba8b99`, 11:29). The Tailor instance was stopped and kept as the record of
  the seam.
- **Saved, measured afterwards:**
  - the gate went from 98 seconds over 2,505 publishing tests to seconds over our own tests, against real Postgres
    instead of SQLite;
  - every file in `app/` is about the job record: 98 tracked files at the end of the window.

## What a client can take from this

This is the engagement's own message applied to our own work. We didn't add a platform to solve the problem; we took
the parts that do the job. It's also a fair picture of how John works with the team: one question, measured, decided,
recorded, and made the default for next time, inside 30 minutes.
