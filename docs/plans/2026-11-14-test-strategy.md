# Test strategy: the POC build (Jen)

| Field | Value |
|---|---|
| Status | Written at sprint start, 2026-11-14 (RTS-4) |
| Plan | `2026-11-13-poc-plan.md`, §2 (acceptance), §4 (rails), §13 |
| Gate | The instance's backend pytest, plus ruff, format and `mypy --strict` on `modules/fieldops` (DOD-1). Evidence goes in `docs/backlog/README.md` per story: command, count, date, sha |

## What we test, and where

| Layer | What | How | Story |
|---|---|---|---|
| Seam | The module is registered, its tables reach the metadata with the prefix, `/health` reads the table, its rows survive export, clear and import | `local-modules/fieldops/backend/tests/test_seam.py`; Tailor's own suites (session scope, portability round trips) run over it too | POC-02 |
| Seed | Deterministic from a seed: same seed, same rows. 45 jobs cover every state; every job has a `job_events` history consistent with its state | pytest over the generator | POC-03 |
| State machine | Every allowed transition succeeds and writes one job row and one event in one transaction; every disallowed transition is refused with a named reason and writes nothing | A table-driven test over the transition table (§5) | POC-04 |
| Rails | Over the cap without approval: no dispatch. No sign-off and no reason: no close. A failed check: no invoice approval. An override succeeds and is recorded with its actor | One test per rail, red first | POC-04 |
| Roles | Each demo role can issue only its own view's commands; `exec@` is read-only | Role client per login, against every command | POC-04 |
| Real time | An event reaches a subscriber after commit, never before; replay: disconnect, change, reconnect with the last id, no gap and no duplicate | WebSocket test client against the app | POC-05 |
| Recommendation | Hard filters (skill, license in the site's state) never violated; the ranking matches 20 hand-checked cases | Eval file, 20 cases, reported as a count | POC-08 |
| Intake drafting | Claude's output validates against the draft schema; on a missing key or a failed call the rule-based fallback runs and is labelled as such | Recorded fixtures for the Claude path; the fallback is pure and tested directly. No live model call in the gate | POC-07 |
| Views | Each narrative's happy path, in a real browser, two contexts: the change made in one appears in the other within a second | Playwright, on the local instance before the deploy (PP-14), then on the box | POC-06..10, POC-17 |

## What we deliberately don't test, and why

- **Live Claude calls in the gate.** They cost money, aren't deterministic, and need the key. The fixtures and the
  fallback are tested; one live call is checked by hand in the dry run.
- **Real QuickBooks, Samsara, FacilIT or any client portal.** They are simulated (plan §7). We test the simulation's
  contract, not a vendor's.
- **Load and scale.** One uvicorn process and a demo's worth of users. The grid's large-data behavior is AG Grid's,
  and isn't the POC's claim.
- **The Postgres downgrade of the `fieldops` branch.** The app role can't drop tables (least privilege), and the migrate
  service only upgrades. The SQLite suites cover the model, and the POC has no uninstall story.
- **Pixel-level visual regression.** Jony reviews the views against the PQ canon by eye. The narratives catch
  behavior.
- **Out-of-scope surfaces (§6, W2).** Option trees, time tracking, parts screens and the rest don't exist, so they have
  nothing to test.
