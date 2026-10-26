#!/usr/bin/env bash
# Stop the web app. Add --all to stop PostgreSQL too (its data is kept). Run from code/.
set -euo pipefail

if [ -f logs/web.pid ]; then
  kill "$(cat logs/web.pid)" 2>/dev/null || true
  rm -f logs/web.pid
  echo "Web app stopped."
else
  echo "Web app is not running."
fi

if [ "${1:-}" = "--all" ]; then
  docker compose stop postgres
fi
