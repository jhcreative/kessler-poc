# POC-06: the frontend shell and the live overview (12:00 to 12:22)

**Goal:** G3, one overview of every job by queue and state, live. And John's rule: TypeScript models that correspond to
the backend's.

## Built

- **The shell:**
  - React Router 7, the house tokens and faces (IBM Plex Sans and Roboto Condensed, from Tailor's library).
  - AG Grid Community 36.2.0, themed to the tokens.
  - Every version pinned exactly, and at least two weeks old.
  - 102 packages, dev tools included.
- **Typed end to end (`scripts/types.sh`):**
  - the backend's OpenAPI is exported offline (no schema is served publicly);
  - the WebSocket frames and every command's payload are added to it;
  - `src/api/schema.ts` is generated from it, and the gate fails if the two drift.
- **The live store (`src/live/`), pure and tested:**
  - connect, buffer, load, then apply;
  - a job only ever moves forward (by its `last_event_id`);
  - reconnect with backoff and replay;
  - a 4401 goes to the sign-in page.
- **The overview:**
  - a tile per state in page 2's queues, with the average wait and the usual time per step (Q9, from `job_events`);
  - the grid newest first;
  - a changed row flashes once.
  - Skeletons appear only after 150 ms (PQ-33).
- **Caddy** serves the views and proxies `/api`, WebSocket included, with noindex, a strict CSP and no `Server`
  header.

## Verified

- The gate ran backend, types, typecheck, unit tests, build and a size budget.
- **The first browser e2e** (Playwright, real Chromium, the real stack behind Caddy) passed 4 tests. One is a
  dispatcher's assignment changing the open overview's row and count in under a second, with no reload. Another fails
  on any console error or CSP violation.

## Found

- **Size:** registering every AG Grid module made 411 KB gzipped. Five modules are registered now, and the grid loads
  only with the views that use it: sign-in is 91 KB, against a 100 KB budget.
- **AG Grid error #200,** a missing module, caught by the e2e's console check.
- **Jony, from the screenshot:** the Paid tile claimed jobs were "waiting". Paid is the end of the line.

## Mineable

- **The clock (Q9) is real data:** "client approval usually takes about a day; billing review about two" comes from
  the seed's histories. It's synthetic: say so.
- **Screenshot:** `docs/evidence/2026-11-14-poc-06-overview.png`.
