#!/usr/bin/env bash
# Backend line and branch coverage (Jen): the gate's pytest run, measured. Reports; it doesn't gate.
# Needs the compose Postgres up, as the gate does. The frontend's screens are covered by the browser e2e, not by lines.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
PG="postgresql+asyncpg://ofs:${POSTGRES_PASSWORD}@127.0.0.1:${LOCAL_PG_PORT}"
cd backend
DATABASE_URL="$PG/ofs" TEST_DATABASE_URL="$PG/ofs_test" .venv/bin/coverage run -m pytest -q -p no:cacheprovider "$@"
.venv/bin/coverage report
