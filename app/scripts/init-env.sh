#!/usr/bin/env bash
# Writes app/.env once, with a generated local Postgres password. Refuses to overwrite.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -e .env ] && { echo ".env exists; leaving it alone"; exit 0; }
umask 077
printf 'POSTGRES_PASSWORD=%s\nLOCAL_WEB_PORT=9219\nLOCAL_PG_PORT=6219\n' "$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')" > .env
echo "wrote .env"
