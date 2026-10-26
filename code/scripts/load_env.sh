#!/usr/bin/env bash
# Load code/.env into the environment. Sourced by start.sh and reset.sh.
# A value with a space after "=" would run as a shell command and print the value
# (a key or a password) in the error, so such a file is refused, naming the
# variable only, never its value.
bad=$(grep -nE '^[A-Za-z_][A-Za-z0-9_]*=[[:space:]]+[^#[:space:]]' .env | cut -d= -f1)
if [ -n "$bad" ]; then
  echo "code/.env: remove the space after '=' on line(s): $bad" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
source .env
set +a
