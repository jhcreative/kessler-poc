# Carry-forward 2026-11-14: Tailor's parts, not a Tailor site; POC-03 done (Anne)

## State

- **John's call** (ADR `docs/adr/2026-11-14-tailor-parts-not-a-tailor-site.md`; agency ADR-0014): actual apps are built
  from Tailor's parts. Admin is users, integrations and config only, and the work happens in one view per role. The
  app is typed end to end, and the same base must work in Node. This supersedes the previous carry-forward's "Start
  here": the Tailor instance and its installer are retired, and the instance stack is stopped.
- **The app:** `app/` at `fbfc9c4`. Backend `app/backend/ofs/`: `states.py` (the state table), `schemas.py` (the
  contract and the typed JSON), `models.py` (ten tables), `rules.py`, `seed.py`, `main.py` (health).
- **POC-03 done.** Evidence is in `docs/backlog/README.md`.

## Start here, next window

1. `cd app && docker compose up -d --wait --build && docker compose exec -T backend python -m ofs.seed`, then
   http://localhost:9219/api/health.
2. The gate: `app/scripts/gate.sh` (needs the compose Postgres up). The venv is `app/backend/.venv`.
3. **POC-04 (Pete, Jen):** `POST /api/jobs/{id}/commands` taking `CommandIn`, checked against `TRANSITIONS`, the roles
   and the rails. Write the job and one `JobEvent` in one transaction, return `JobOut`, refuse with `Refusal`. Then the
   five logins (bcrypt, session cookie), with Orly's RTS-6 notes in `docs/backlog/2026-11-14-sprint-start.md`.
4. **A schema change** means editing `models.py`, then `alembic revision --autogenerate`, reviewing the file, and
   letting the gate's `alembic check` confirm it.
5. **Before the Claude drafting call (POC-07):** load the `claude-api` skill. Use the key in
   `~/jhc/secrets/anthropic.env` (John).
