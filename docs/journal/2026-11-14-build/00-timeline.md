# Timeline, 2026-11-14 (Eastern)

Times are commit times. The window started just after 10:00, from the handoff
`docs/carry-forward/2026-11-14-plan-approved-handoff.md`.

## Engagement repo (`~/jhc/prospects/kessler-poc`)

| Time | Commit | Story | What landed |
|---|---|---|---|
| 10:20 | `e42c951` | Sprint start, POC-02 | RTS-1..6 recorded; the test strategy; the first POC-02 (a module inside a Tailor instance) |
| 11:18 | `6ce60e4` | POC-07 prep | John: the demo uses the existing Anthropic key |
| 11:29 | `dba8b99` | POC-02 again, POC-03 | The app rebuilt on Tailor's parts (John's call); ten typed tables, the state table, the seed |
| 11:29 | `4dcd59a` | POC-03 | Evidence; the plan amended by the new ADR |
| 11:44 | `0cbe04e` | POC-04 | Commands, the rails, the five logins |
| 11:45 | `5c2a4ab` | POC-04 | Evidence |
| 11:59 | `77b2dad` | POC-05 | The hub, the WebSocket, replay |
| 11:59 | `20038be` | POC-05 | Evidence; the demo passwords moved into `~/jhc/secrets` (John's yes) |
| 12:21 | `87060be` | POC-06 | The frontend shell, typed end to end; the live overview |
| 12:22 | `f44d64d` | POC-06 | Evidence and the first screenshot |
| 13:16 | `07c9baa` | POC-07 | The coordinator workspace; Claude drafting intake |
| 13:18 | `4f34059` | POC-07 | Evidence; ADR: Claude drafts intake |
| 13:30 | `49b35c0` | POC-08 | Dispatch and the recommendation |
| 13:37 | `85f625d` | POC-08 | Two e2e flakes understood and fixed |
| 13:39 | `3003f23` | POC-08 | Evidence |
| 14:14 | `d354719` | POC-09 | The tech's phone |
| 14:16 | `be7b00d` | POC-09 | Evidence |
| 14:32 | `432ed61` | POC-10, POC-14 | The controller, QuickBooks (simulated), aging |
| 14:34 | `77248a3` | POC-10, POC-14 | Evidence; every view built |
| 15:10 | `9d29152` | POC-11 | The box path: the edge override, the ship script, the live check |
| 15:25 | `aa8594a` | POC-11 | The cold review: 17 fixed, 3 accepted |
| 15:29 | `dcb90f6` | POC-11 | Evidence; the local half done |

## The first Tailor instance (`~/jhc/sites/jahnel-poc`, retired at 11:2x)

| Time | Commit | What |
|---|---|---|
| 10:04 | `21def9f` | The scaffold's own commit (Tailor v1.1.5) |
| 10:19 | `669bada` | `fieldops` mounted through Tailor's installer: the seam proven, then retired (see `02-…`) |

## Agency repo (`~/jhc/jhc-agency`)

| Time | Commit | What |
|---|---|---|
| 11:24 | `e280911` | ADR-0014: actual apps are built from Tailor's parts; TEAM-11 opened |
| 11:29 | `e37f9ab` | ADR-0014 amended: typed end to end; the same base in Node |
| 10:20 to 15:29 | 10 commits | `docs/for-john.md` regenerated after every status change (PP-17) |

## The rhythm

Every story closed the same way:
1. code and tests;
2. the gate (and from POC-06 on, the browser e2e);
3. a screenshot read for form (Jony);
4. a commit naming the evidence;
5. a second commit with the backlog evidence, status and a carry-forward note;
6. the inbox regenerated.

That's PP-17's routine, run per story. It's why a later session can pick up from any commit.
