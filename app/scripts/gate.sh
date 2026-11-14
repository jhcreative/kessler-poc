#!/usr/bin/env bash
# The local gate (DOD-1): lint, format, types, the migrations match the models, tests on Postgres.
# Needs the compose Postgres up: docker compose up -d postgres
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
PG="postgresql+asyncpg://ofs:${POSTGRES_PASSWORD}@127.0.0.1:${LOCAL_PG_PORT}"
docker compose exec -T postgres sh -c "psql -U ofs -d ofs -tAc \"SELECT 1 FROM pg_database WHERE datname='ofs_test'\" | grep -q 1 || createdb -U ofs ofs_test"
cd backend
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
DATABASE_URL="$PG/ofs" .venv/bin/alembic upgrade head
DATABASE_URL="$PG/ofs" .venv/bin/alembic check
DATABASE_URL="$PG/ofs" TEST_DATABASE_URL="$PG/ofs_test" .venv/bin/pytest -q -p no:cacheprovider "$@"
echo "gate: green at $(git rev-parse --short HEAD) $(date -u +%FT%TZ)"
