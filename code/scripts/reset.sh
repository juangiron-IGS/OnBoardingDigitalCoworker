#!/usr/bin/env bash
# Recreate the PostgreSQL volume and reload migrations, roles and seed data. Run from code/.
set -euo pipefail

set -a; source .env; set +a

docker compose down --volumes
docker compose up -d --wait postgres
./scripts/apply_db.sh
