# Sprint start and the first POC-02 (10:00 to 10:20)

## The sprint-start gate (RTS-1..6)

The committed stories were POC-02 to POC-11, ranks 3 to 12, the protected set. Angela and Anne checked each Ready to
Start gate against the plan and against what was on disk. The record is `docs/backlog/2026-11-14-sprint-start.md`.

| Gate | Result |
|---|---|
| RTS-1 Requirements are testable | Pass. POC-02's acceptance was made exact before the build |
| RTS-2 The contract is defined | Pass for POC-02; owed for POC-03 and POC-04. Paid at 11:29, when the schemas were written first |
| RTS-3 Dependencies are identified | Pass. The box, DNS and the repo wait on John and block only the deploy |
| RTS-4 Test strategy exists | It didn't, so Jen wrote one: `docs/plans/2026-11-14-test-strategy.md`, including what we deliberately don't test |
| RTS-5 The branch is clean | Pass |
| RTS-6 Privacy goes to Orly first | Pass. Orly's design notes bind POC-03 to POC-05: roles checked on the server, no mail to ofs.com, the WebSocket authenticated, noindex |

**What a client can take from this:** the gate stopped one thing, the missing test strategy, and it was fixed in
minutes rather than discovered at review.

## The first POC-02: a module inside a Tailor instance

The handoff's plan was to scaffold a full Tailor site and mount the POC as an instance-local own-tables module called
`fieldops`. That was risk R3 ("mounting a local module in an instance is unproven").

**What happened:**
- **The scaffold** (`node ~/jhc/tailor/scaffold/scaffold.js`, Tailor v1.1.5) produced `~/jhc/sites/jahnel-poc` at
  `21def9f`.
- **Q7 found its answer:** Tailor's installer reads modules only from Tailor's own `modules/` directory. So
  `scripts/install-local-modules.mjs` gave Tailor's real `installModules` an overlay root, holding the instance's
  Tailor modules and its local one side by side. The generated registration was byte for byte what `--module`
  writes, Tailor's own `email` module re-vendored with zero diff, and a rerun wrote the same bytes.
- **The gate caught two real defects** on the way, both Tailor contracts:
  - a request-scoped session (Tailor ADR-0102 needs function scope);
  - a missing Path P export hook, which made Tailor's own portability suites fail.
- **The result:** 2,505 tests passed, at `669bada`.
- **A guard fired on a real race:** another window moved Tailor's shared `develop` checkout mid-session. The installer
  refused to run against a Tailor that didn't match the instance's recorded version. We used a read-only `git archive`
  of the right version instead, and never touched the other window's checkout (PP-13).

**Why it was retired an hour later:** see `02-tailor-parts-not-a-tailor-site.md`. The seam worked. What changed was
the question of whether the POC should live inside a publishing platform at all.

**What a client can take from this:** we proved the risky path before betting on it, and when the evidence said a
simpler shape was better, we changed course in under an hour without losing the work. The data model, the contract
files and the lessons (session scope, export hooks) carried straight over.
