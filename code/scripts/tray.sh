#!/usr/bin/env bash
# Coworker Tray: the Onboarding Coworker in the Windows notification area. Run from
# code/ after ./scripts/start.sh. COWORKER_TRAY_ROLE picks the first role (default
# recruiter); the tray menu changes it. Needs: pip install -e ".[tray]".
set -euo pipefail

source scripts/load_env.sh

PY=.venv/Scripts/pythonw.exe
[ -x "$PY" ] || PY=.venv/Scripts/python.exe
[ -x "$PY" ] || PY=.venv/bin/python
"$PY" -m desktop.tray &
echo "Coworker Tray started: look for the blue icon next to the clock."
