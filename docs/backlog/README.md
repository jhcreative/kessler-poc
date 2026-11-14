# Backlog

Ranked top first. The plan is `docs/plans/2026-11-13-poc-plan.md`, and its §2 holds the acceptance criteria (G, C, D, T
and B). Ranks 1–12 are protected. Ranks 13–16 are planned, and are the first cut if we slip (plan §10).

| Rank | ID | Story | Acceptance | Owner | State |
|---|---|---|---|---|---|
| 1 | POC-00 | Intake: the round-4 account, the step-5 brief, the due date | Discovery, flows, deck | Angela | Done (11-13) |
| 2 | POC-01 | Approve the plan; walkthrough Q1–Q11 | T3 | John | Done (11-14) |
| 3 | POC-02 | Scaffold the Tailor instance and the `fieldops` module seam (Q7) | Instance boots locally; module mounted | Cesar | Done (11-14) |
| 4 | POC-03 | Tables, migrations, states, and the synthetic seed (§5, §7) | 45 jobs over every state; history in `job_events` | Pete, Jen | Ready |
| 5 | POC-04 | Commands, the state machine and the rails, with tests | Every transition and rail tested | Pete, Jen | Ready |
| 6 | POC-05 | WebSocket hub, topics, and replay on reconnect | G1; the replay test passes | Pete | Ready |
| 7 | POC-06 | Overview: every job by queue and state, live | G3 | Nathan | Ready |
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
