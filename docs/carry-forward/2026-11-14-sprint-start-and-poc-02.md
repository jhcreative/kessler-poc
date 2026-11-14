# Carry-forward 2026-11-14: sprint start passed; POC-02 done (Anne)

## State

- **Sprint start:** RTS-1..6 passed for the committed stories (`docs/backlog/2026-11-14-sprint-start.md`). RTS-2 is
  still owed for POC-03 and POC-04: Pete's command and event schemas come first. Orly's RTS-6 notes bind POC-03 to
  POC-05.
- **Test strategy:** `docs/plans/2026-11-14-test-strategy.md` (Jen).
- **POC-02 done.** Instance `~/jhc/sites/jahnel-poc` at `669bada`, running at http://localhost:9219. Backend pytest
  2505 passed, 7 skipped. Evidence is in `docs/backlog/README.md`.
- **Q7 answered:** `local-modules/fieldops/` is installed by `scripts/install-local-modules.mjs`, which runs Tailor's
  own installer over an overlay root. No POC code in Tailor core.

## Start here, next window

1. **Re-run the installer after every change under `local-modules/`.** Tailor's `develop` has moved past `3d53021e`,
   so point it at an archive and leave the shared checkout alone (PP-13):
   ```sh
   D=<scratch dir>; git -C ~/jhc/tailor archive 3d53021eaea1 scaffold/lib modules | tar -x -C "$D"
   cd ~/jhc/sites/jahnel-poc && TAILOR_ROOT="$D" TAILOR_SHA_OK=1 node scripts/install-local-modules.mjs
   ```
2. **The gate:** `cd backend && .venv/bin/python -m pytest -q` (the venv exists), then ruff, format and
   `mypy --strict modules/fieldops`. Rebuild with `docker compose -f docker-compose.yml -f docker-compose.local.yml up
   -d --wait --build`.
3. **POC-03 (Pete, Jen):** schemas first (RTS-2), then the rest of plan §5. Each new table goes into `models.py`, a new
   migration on the `fieldops` branch (`down_revision = "20261114_fo01"`, plus `depends_on` for any core table it
   references, such as users), and `_TABLES` in `portability.py`, parents first.
4. **Before the Claude drafting call (POC-07):** load the `claude-api` skill.

## Lessons from this session

- **Two Tailor contracts every module meets:** a session dependency at function scope (ADR-0102), and a Path P hook
  (`portability.py`: export, clear, import; ADR-0053). Tailor's own suites catch both once the module is installed.
- **DDL runs as the migrate role.** The app role can't drop tables, and the migrate service only upgrades.
