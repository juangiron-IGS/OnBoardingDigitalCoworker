#!/usr/bin/env bash
# Apply migrations, then roles, then synthetic seed data to the local PostgreSQL.
# Called by start.sh (new volume only), reset.sh and CI. Run from code/.
set -euo pipefail

: "${DB_PORT:?DB_PORT is not set}"
: "${DB_NAME:?DB_NAME is not set}"
: "${DB_ADMIN_PASSWORD:?DB_ADMIN_PASSWORD is not set}"
: "${DB_APP_PASSWORD:?DB_APP_PASSWORD is not set}"
: "${DB_AUDIT_PASSWORD:?DB_AUDIT_PASSWORD is not set}"

export PGPASSWORD="${DB_ADMIN_PASSWORD}"
PSQL=(psql -h 127.0.0.1 -p "${DB_PORT}" -U postgres -d "${DB_NAME}" -v ON_ERROR_STOP=1 -q)

shopt -s nullglob
for f in db/migrations/*.sql; do "${PSQL[@]}" -f "$f"; done
for f in db/roles/*.sql; do
  "${PSQL[@]}" -v app_password="${DB_APP_PASSWORD}" -v audit_password="${DB_AUDIT_PASSWORD}" -f "$f"
done
for f in db/seed/*.sql; do "${PSQL[@]}" -f "$f"; done

echo "Database ready: migrations, roles and seed data applied."
