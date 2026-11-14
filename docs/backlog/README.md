# Backlog

Ranked top first. The plan is `docs/plans/2026-11-13-poc-plan.md`, and its §2 holds the acceptance criteria (G, C, D, T
and B). Ranks 1–12 are protected. Ranks 13–16 are planned, and are the first cut if we slip (plan §10).

| Rank | ID | Story | Acceptance | Owner | State |
|---|---|---|---|---|---|
| 1 | POC-00 | Intake: the round-4 account, the step-5 brief, the due date | Discovery, flows, deck | Angela | Done (11-13) |
| 2 | POC-01 | Approve the plan; walkthrough Q1–Q11 | T3 | John | Done (11-14) |
| 3 | POC-02 | The app skeleton on Tailor's parts (ADR `2026-11-14-tailor-parts-not-a-tailor-site.md`) | Boots locally; health reads the database | Cesar | Done (11-14), rebuilt lean |
| 4 | POC-03 | Tables, migrations, states, and the synthetic seed (§5, §7) | 45 jobs over every state; history in `job_events` | Pete, Jen | Done (11-14) |
| 5 | POC-04 | Commands, the state machine and the rails, with tests; the five role logins | Every transition and rail tested | Pete, Jen, Orly | Done (11-14) |
| 6 | POC-05 | WebSocket hub, topics, and replay on reconnect | G1; the replay test passes | Pete | Done (11-14) |
| 7 | POC-06 | Overview: every job by queue and state, live; the frontend shell, with TS types generated from the API's OpenAPI | G3; the gate fails if the TS drifts from the backend | Nathan | Done (11-14) |
| 8 | POC-07 | Coordinator workspace: all, mine, single job, drafts, approve for dispatch | C1, C2 | Nathan, Pete | Ready |
| 9 | POC-08 | Dispatch: arrivals, the recommended tech with reasons, assign | D1–D3 | Nathan, Jen | Ready |
| 10 | POC-09 | Tech phone view: my queue, the schedule, complete, needs review | T1–T3 | Nathan | Ready |
| 11 | POC-10 | Controller queue: billing queue, approve and submit to QuickBooks (simulated) | B1, B2 | Nathan, Pete | Ready |
| 12 | POC-11 | Gate, cold review, deploy dry run to OVH (edge mode, IMAGES=local) | DOD-1, DOD-3; R1 verified | Cesar, Orly, Rob | Ready |
| 13 | POC-12 | Needs-review decisions: reassign or ask to wait | T4 | Pete, Nathan | Planned; cut first if we slip |
| 14 | POC-13 | Client approval when a rule fires | C3 | Pete, Nathan | Planned; cut first if we slip |
| 15 | POC-14 | QuickBooks aging summary in the controller view | B3 | Jen, Nathan | Planned; cut first if we slip |
| 16 | POC-15 | Simulator: live arrivals and truck movement; pause, resume, reset | §7 | Jen | Planned; cut first if we slip |
| 17 | POC-17 | Playwright narratives N1–N4, recorded, captioned and uploaded unlisted to John's YouTube | Plan §11 | Jen, Henry, John | Monday |
| 18 | POC-18 | Stretch: in-app help panel playing each view's narrative | Plan §11a | Nathan | Stretch |
| 19 | POC-16 | Deploy on John's go, the demo script rehearsal, README, the email | Monday | Rob, Angela, Lisa | Monday |

## Evidence (DOD-1)

Sprint start, RTS-1..6: `2026-11-14-sprint-start.md`.

**POC-02, 2026-11-14, instance `~/jhc/sites/jahnel-poc` at `669bada`** (Tailor v1.1.5, `3d53021e`):
- `cd backend && .venv/bin/python -m pytest -q`: **2505 passed, 7 skipped**, 0 failed. That count includes the 4
  fieldops seam tests and Tailor's own session-scope and portability round trips, which run over the module.
- `ruff check`, `ruff format --check` and `mypy --strict` on `modules/fieldops`: clean.
- The running stack: every container healthy, `/` 200, `GET /api/modules/fieldops/health` 200
  (`{"module":"fieldops","installed":true,"clients":0}`), `alembic heads` lists `20261114_fo01 (fieldops)`.

**Q7 answered (risk R3 retired), the seam.** Tailor's scaffold installs modules only from `~/jhc/tailor/modules`, so a
module that lives in the instance needs a step after the scaffold. `scripts/install-local-modules.mjs` gives
Tailor's own `installModules` an overlay root holding the instance's Tailor modules and `local-modules/*` side by side.
The generated registration is exactly what `--module fieldops` would write. Tailor's `email` re-vendored with zero
diff, and a rerun writes the same bytes. It refuses unless the Tailor source is at `tailor.json`'s `tailorSha`; the
guard fired once this session when another window moved Tailor's `develop`, and the run used a `git archive` of
`3d53021e` instead. No POC code in Tailor core. The fallback (plain instance routes) wasn't needed.

The gate caught two real defects on the way, both fixed. The route took a request-scoped session (Tailor ADR-0102
needs function scope). The module also had no Path P hook, so exports wrote `__exporter__: absent` and imports
refused; `portability.py` now exports, clears and imports every fieldops table.

**A candidate for Tailor after Monday (Cesar):** a `--local-module <dir>` on the scaffold, so this overlay becomes a
flag. That's a Tailor story, not POC work.

**POC-02 rebuilt, and POC-03, 2026-11-14, `app/` at `dba8b99`.** John's call: Tailor's parts, not a Tailor site (ADR
`2026-11-14-tailor-parts-not-a-tailor-site.md`; agency ADR-0014). The first POC-02 above stays as the record of the
instance-module seam. Its instance (`~/jhc/sites/jahnel-poc`) is stopped, and nothing in `app/` depends on it.
- `app/scripts/gate.sh`: ruff, format, `mypy --strict`, `alembic check` (the migration matches the models), and pytest
  on Postgres: **20 passed in 2.9 s**, `gate: green at dba8b99 2026-11-14T16:29:22Z`.
- The running stack (`docker compose up -d --wait --build`, then `python -m ofs.seed`): `clients=8 contracts=8
  sites=60 people=16 techs=10 fleet_positions=10 jobs=45 job_events=260 invoices=15 qb_ledger=158`;
  `GET http://localhost:9219/api/health` 200, `{"jobs":45,"events":260}`.
- The acceptance, as tests: all 11 states on the board, in the planned counts. Every history is legal under the
  state table, in time order, ends at the job's state and before now. The three hard rails already hold in the seed.
  Every ready job has a tech to recommend. Every aging bucket is non-empty. The same seed gives the same world, and
  FacilIT is a channel, not a client.
- **Typed end to end** (John): the enums, the API contract, every JSON column (rules, approval, sign-off, invoice lines)
  and one payload model per command, all checked on write. The TypeScript side comes with POC-06.

**POC-04, 2026-11-14, `app/` at `0cbe04e`.** `app/scripts/gate.sh`: **58 passed in 23.6 s** on Postgres; ruff, format,
`mypy --strict` and `alembic check` clean (`gate: green at 0cbe04e 2026-11-14T16:45:05Z`).
- **Every transition:** each person-issued command is refused from every wrong state, with nothing written. Roles are
  refused by name, a tech acts only on their own job, and a stale view gets a 409.
- **The rails:** the three hard rails are refused even with an override reason. The soft rail (assigning outside a
  tech's skill or license) passes with a reason, and the reason is on the event.
- **The happy path over HTTP** (N1 to N3), with real logins: intake draft, qualify, approve for dispatch, assign, arrive,
  update fields, close, the invoice drafted at close, approve, and a QuickBooks (simulated) row. The test checks the
  nine-event history and who did each step.
- **Auth:** HttpOnly and SameSite=Lax cookie, Secure by default; failures read the same for a wrong password and an
  unknown email; rate limit 429; a disabled login stops at once; exec is read-only; a cross-site POST is refused.
- **On the running stack:** `coord@ofs.com` signs in, `/api/auth/me` answers, and `/api/jobs?mine=true` returns 18 jobs.
- **A seed defect found and fixed:** 33 of 45 jobs were over their client's cap, against plan §7's "a few". It's now
  pinned by a test (3 to 12, and the drafts include one with no rule).

**POC-05, 2026-11-14, `app/` at `77b2dad`.** `app/scripts/gate.sh`: **67 passed in 23.3 s**
(`gate: green at 77b2dad 2026-11-14T16:59:36Z`). The socket tests run against a real uvicorn server with real
WebSocket clients and cookies.
- **G1:** a change made by the dispatcher reaches the coordinator's open view in under a second, with the job's new
  state and who did it. On the running stack it took **21 ms** (job 1013 assigned, event 227).
- **Replay:** a view that reconnects with its last id gets exactly what it missed, in order, then live events, with
  nothing twice.
- **Scoping:** a tech hears only their own jobs, live and in replay, and hears a job arrive on their schedule (T1).
- **Honest publishing:** a refused command publishes nothing; publishing runs only after the commit.
- **Refusals and upkeep:** no cookie is 4401; another site's Origin is 4403; a view too far behind gets resync (4409);
  an idle socket is pinged and its login re-checked; a closed view leaves the hub at once.
- **Found by the gate's run time:** the suite took 326 s because a socket missed its client's close until the next
  ping. Fixed, and pinned by a test.
- **Still open (R1):** the first WebSocket through edge-mode Caddy on the box. That's the POC-11 dry run.

**POC-06, 2026-11-14, `app/` at `87060be`.**
- `app/scripts/gate.sh`, `gate: green at 87060be 2026-11-14T17:22:04Z`:
  - backend: 69 passed;
  - `types.sh --check`: the TS is in step with the backend;
  - typecheck (app and e2e) and vitest: 6 passed;
  - build, and the budget: sign-in entry 90,966 of 100,000 bytes gzipped; the grid chunk 234,597 of 250,000.
- `app/scripts/e2e.sh` (PP-14), Playwright in real Chromium against the real stack (Caddy, backend, Postgres):
  **4 passed**, `e2e: green at 87060be 2026-11-14T17:22:33Z`.
  - The exec signs in to all 45 jobs and 11 state tiles, filters and clears, with no console error and no CSP
    violation.
  - A dispatcher's assignment changes the open overview's row and the Assigned count in under a second, with no
    reload (G1, G3).
  - A tech is sent to their own view; signing out ends the session.
- **Typed end to end:** the TS comes from the backend's OpenAPI, the WebSocket frames included. The schema isn't
  served (`/openapi.json` is a 404); it's exported offline.
- **Found on the way:**
  - registering every AG Grid module made 411 KB gzipped, so only five modules are registered now, and the grid
    loads on demand;
  - AG Grid error #200 (a missing cell-style module), caught by the e2e's console check;
  - the Paid tile claimed jobs were "waiting" (Jony, from the screenshot).
- Screenshot: `docs/evidence/2026-11-14-poc-06-overview.png`.
