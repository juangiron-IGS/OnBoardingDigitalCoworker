#!/usr/bin/env bash
# Single-command start (Tech Doc §4.4). Run from code/, in Git Bash or WSL on Windows.
# 1. container runtime  2. PostgreSQL  3. database setup on a new volume
# 4. web app with the Orchestrator and agents on 127.0.0.1  5. health check
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

PY=.venv/Scripts/python.exe
[ -x "$PY" ] || PY=.venv/bin/python
mkdir -p logs

if [ -f logs/web.pid ] && kill -0 "$(cat logs/web.pid)" 2>/dev/null; then
  echo "Web app already running (pid $(cat logs/web.pid))."
else
  nohup "$PY" -m web.api.main > logs/web.log 2>&1 &
  echo $! > logs/web.pid
fi

"$PY" scripts/health_check.py
echo "Open http://127.0.0.1:${WEB_APP_PORT:-3000} · stop with ./scripts/stop.sh · logs in code/logs/"
