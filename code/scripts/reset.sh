#!/usr/bin/env bash
# Recreate the PostgreSQL volume and reload migrations, roles and seed data. Run from code/.
set -euo pipefail

set -a; source .env; set +a

docker compose down --volumes
docker compose up -d --wait postgres
./scripts/apply_db.sh

# A separate database for the test suite, so manual runs never collide with tests.
docker compose exec -T postgres createdb -U postgres "${DB_NAME}_test"
DB_NAME="${DB_NAME}_test" ./scripts/apply_db.sh
