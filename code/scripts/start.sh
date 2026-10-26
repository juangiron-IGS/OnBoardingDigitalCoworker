#!/usr/bin/env bash
# Single-command start (Tech Doc §4.4). Run from code/, in Git Bash or WSL on Windows.
# 1. container runtime  2. PostgreSQL  3. database setup on a new volume
# 4. MCP servers when AGENT_TRANSPORT=mcp  5. web app with the Orchestrator and agents
# 6. health check. Everything binds to 127.0.0.1.
set -euo pipefail

source scripts/load_env.sh

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

# Start one process in the background unless its pid file points to a live one.
launch() {
  local name="$1" module="$2"
  if [ -f "logs/$name.pid" ] && kill -0 "$(cat "logs/$name.pid")" 2>/dev/null; then
    echo "$name already running (pid $(cat "logs/$name.pid"))."
  else
    nohup "$PY" -m "$module" > "logs/$name.log" 2>&1 &
    echo $! > "logs/$name.pid"
  fi
}

if [ "${AGENT_TRANSPORT:-in_process}" = "mcp" ]; then
  launch jobdiva-read mcp_servers.jobdiva_read.server
  launch jobdiva-workflow mcp_servers.jobdiva_workflow.server
  launch teams-mock mcp_servers.mocks.teams.server
fi
launch web web.api.main

"$PY" scripts/health_check.py
echo "Open http://127.0.0.1:${WEB_APP_PORT:-3000} · stop with ./scripts/stop.sh · logs in code/logs/"
