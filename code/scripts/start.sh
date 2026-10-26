#!/usr/bin/env bash
# Single-command start (Tech Doc §4.4). Run from code/.
# Steps 1-3 (container runtime, PostgreSQL, database setup) are in place.
# Steps 4-5 (start every process on 127.0.0.1 and run health_check.py) are added in Task D1.
set -euo pipefail

set -a; source .env; set +a

if ! docker info >/dev/null 2>&1; then
  echo "Container runtime not running. Start Docker or Podman and run this again." >&2
  exit 1
fi

new_volume=false
if ! docker volume inspect "$(basename "$PWD")_coworker_pgdata" >/dev/null 2>&1; then
  new_volume=true
fi

docker compose up -d --wait postgres

if [ "$new_volume" = true ]; then
  ./scripts/apply_db.sh
  docker compose exec -T postgres createdb -U postgres "${DB_NAME}_test"
  DB_NAME="${DB_NAME}_test" ./scripts/apply_db.sh
fi
