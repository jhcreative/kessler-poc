# Build journal, 2026-11-14: from the approved plan to the deploy (Anne)

One working window on Saturday 2026-11-14, about 10:00 to 15:30 Eastern. It started at the approved plan and ended
with every view built, the app hardened by a cold review, and one command ready to deploy it. The deploy itself waits
on the box (John's items in `docs/status.md`).

**Who this is for:** future sessions writing client-facing material (the README, the recap email to Neale and
Ann-Marie, narration for the Playwright videos, a case study), and Jahnel, who reads the process record alongside the
POC (CLAUDE.md: "track every effort and deliver superb documentation of our process").

**How it's written:** every fact here is checkable. Each one comes from a commit, a test run, a measurement or John's
own words, and the source is named. Nothing is rounded up. Where something isn't proven yet, it says so.

## The files

| File | What it holds |
|---|---|
| `00-timeline.md` | The window hour by hour: every commit, in all three repos |
| `01-sprint-start-and-the-first-poc-02.md` | RTS-1..6, the test strategy, and the Tailor-instance build we then retired |
| `02-tailor-parts-not-a-tailor-site.md` | John's call to build from Tailor's parts, and the agency pattern it became (ADR-0014) |
| `03-poc-03-the-job-record.md` | The typed data model, the state table, the deterministic seed |
| `04-poc-04-commands-and-logins.md` | Commands, the rails, the five role logins |
| `05-poc-05-live-updates.md` | The hub, the WebSocket, replay on reconnect (G1) |
| `06-poc-06-overview-and-types.md` | The frontend shell, typed end to end, the live overview (G3) |
| `07-poc-07-coordinator-and-claude.md` | The coordinator workspace and Claude drafting intake (C1 to C3) |
| `08-poc-08-dispatch.md` | Dispatch with the recommended tech and the reasons (D1 to D3, T4) |
| `09-poc-09-the-techs-phone.md` | The field app (T1 to T3) |
| `10-poc-10-and-14-the-controller.md` | Billing, QuickBooks (simulated) and aging (B1 to B3) |
| `11-poc-11-hardening-and-the-box-path.md` | The gate, the cold review, Orly's checks, the ship script, R1's check |
| `12-the-box-and-the-first-deploy.md` | 2026-11-16: the apps box, the secrets, the first deploy and its one stop, 7 of 7 live |
| `decisions.md` | Every decision John made in the window, in his words, and where it's recorded |
| `defects.md` | Every defect found, what found it, and the fix |
| `numbers.md` | The measurements: tests, timings, sizes, cost |
| `mining-guide.md` | How to turn this into client-facing documents: what to say, what evidence backs it, what not to claim yet |

## Stories covered

POC-02, POC-03, POC-04, POC-05, POC-06, POC-07, POC-08, POC-09, POC-10 and POC-11's local half. Also, below the cut
line: POC-12 (T4), POC-13 (C3) and POC-14 (B3). Not covered: POC-15 (the simulator), POC-16 (the deploy, Monday) and
POC-17 and POC-18 (the narratives and the help panel).

## The sources this journal stands on

- **The plan:** `docs/plans/2026-11-13-poc-plan.md` (approved, T3), amended by
  `docs/adr/2026-11-14-tailor-parts-not-a-tailor-site.md`.
- **Evidence per story:** `docs/backlog/README.md` (the "Evidence (DOD-1)" sections).
- **Session notes:** `docs/carry-forward/2026-11-14-*.md`.
- **Screenshots:** `docs/evidence/2026-11-14-poc-*.png`.
- **The cold review:** `docs/backlog/2026-11-14-cold-review.md`.
- **The code:** `app/` at `2647b34`. The gate and e2e last ran on the identical tree at `c41d5c5`.
