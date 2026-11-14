#!/usr/bin/env bash
# Writes app/.env once, with a generated local Postgres password. Refuses to overwrite.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -e .env ] && { echo ".env exists; leaving it alone"; exit 0; }
umask 077
gen() { python3 -c "import secrets; print(secrets.token_urlsafe($1))"; }
printf 'POSTGRES_PASSWORD=%s\nSESSION_SECRET=%s\nCOOKIE_SECURE=0\nALLOWED_ORIGINS=http://localhost:9219\nLOCAL_WEB_PORT=9219\nLOCAL_PG_PORT=6219\n' "$(gen 24)" "$(gen 48)" > .env
echo "wrote .env"
