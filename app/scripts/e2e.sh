#!/usr/bin/env bash
# The instance e2e (PP-14): rebuild the stack, reseed it, restore the logins, and drive it in a real browser.
set -euo pipefail
cd "$(dirname "$0")/.."
LOGINS="${E2E_LOGINS:-$HOME/jhc/secrets/jahnel-poc/local-demo-logins.env}"
set -a; . ./.env; set +a
docker compose up -d --wait --build >/dev/null
# A fresh backend process: the login rate limit lives in memory, and back-to-back runs from one address would hit it.
docker compose restart backend >/dev/null && docker compose up -d --wait >/dev/null
docker compose exec -T backend python -m ofs.seed
(cd backend && DATABASE_URL="postgresql+asyncpg://ofs:${POSTGRES_PASSWORD}@127.0.0.1:${LOCAL_PG_PORT}/ofs" .venv/bin/python -m ofs.logins --file "$LOGINS")
(cd frontend && E2E_LOGINS="$LOGINS" npx --no-install playwright test "$@")
echo "e2e: green at $(git rev-parse --short HEAD) $(date -u +%FT%TZ)"
