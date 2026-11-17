#!/usr/bin/env bash
# One take of the demo video (D4): reseed the LOCAL stack the way app/scripts/e2e.sh does, restore the logins, and run
# record.mjs. Retake (exit 3) until the drafted request's recommended tech is Tech 1 and Claude drafted it.
# Usage: take.sh <take-dir> [max-tries]
set -euo pipefail
cd "$(dirname "$0")/../.."
TAKE="${1:?take dir}"; TRIES="${2:-25}"
LOGINS="${E2E_LOGINS:-$HOME/jhc/secrets/jahnel-poc/local-demo-logins.env}"
set -a; . ./.env; set +a
for i in $(seq 1 "$TRIES"); do
  # A fresh backend process: the login and new-request limits live in memory.
  docker compose restart backend >/dev/null && docker compose up -d --wait >/dev/null
  docker compose exec -T backend python -m ofs.seed >/dev/null
  (cd backend && DATABASE_URL="postgresql+asyncpg://ofs:${POSTGRES_PASSWORD}@127.0.0.1:${LOCAL_PG_PORT}/ofs" .venv/bin/python -m ofs.logins --file "$LOGINS" >/dev/null)
  rm -rf "$TAKE"; mkdir -p "$TAKE"
  set +e
  (cd frontend && TAKE_DIR="$TAKE" E2E_LOGINS="$LOGINS" node video/record.mjs)
  code=$?
  set -e
  rm -rf "$TAKE/raw"
  if [ "$code" -eq 0 ]; then
    (cd "$TAKE" && shasum -a 256 *.webm events.json > MANIFEST.sha256)
    echo "take: done on try $i, $TAKE"; exit 0
  fi
  [ "$code" -eq 3 ] || { echo "take: failed (exit $code) on try $i"; exit "$code"; }
  echo "take: retake ($i)"
done
echo "take: no usable take in $TRIES tries"; exit 4
