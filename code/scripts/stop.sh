#!/usr/bin/env bash
# Stop the web app and the MCP servers. Add --all to stop PostgreSQL too (its data is
# kept). Run from code/.
set -euo pipefail

stopped=false
for name in web jobdiva-read jobdiva-workflow teams-mock; do
  if [ -f "logs/$name.pid" ]; then
    kill "$(cat "logs/$name.pid")" 2>/dev/null || true
    rm -f "logs/$name.pid"
    echo "$name stopped."
    stopped=true
  fi
done
[ "$stopped" = true ] || echo "Nothing was running."

if [ "${1:-}" = "--all" ]; then
  docker compose stop postgres
fi
