---
name: run-coworker-locally
description: Starting, checking, resetting and stopping the Onboarding Digital Coworker on a local machine so it can be tested by hand or by script. Use before any manual walkthrough, performance run or UI check, or when the app does not come up.
---

# Run the Coworker locally

Everything runs from `code/` in **Git Bash** (the scripts are bash; PowerShell will not run them). The README has the full installation text; this is the test-time checklist.

Prerequisites: Python 3.12 or later in `code/.venv` (`pip install -e ".[dev]"`; on this machine use the uv Python 3.14 if `python` is 3.11), Docker Desktop **running**, and `code/.env` copied from `.env.example` with the three DB passwords set and put inside `DATABASE_URL` and `AUDIT_DATABASE_URL`. `.env` is git-ignored; never print its values.

Commands:
- `./scripts/start.sh`: PostgreSQL, migrations on a new volume, MCP servers (when `AGENT_TRANSPORT=mcp`), web app, health check. Success ends with `web app: ok · database: ok · transport: mcp · JobDiva: mock · model: rules · MCP: ... ok`. Then http://127.0.0.1:3000.
- `./scripts/stop.sh` (`--all` also stops PostgreSQL; data kept). `./scripts/reset.sh`: **destroys** the local database and reloads the seed; use it after any pull that adds a migration.
- Health: `GET http://127.0.0.1:3000/api/health`. Logs: `code/logs/*.log`.

Settings that change test results (record them in every result): `MODEL_PROVIDER` (`rules` for reproducible runs; `claude` needs a key and adds model latency and variation), `AGENT_TRANSPORT` (`mcp` or `in_process`), `JOBDIVA_MODE` (`mock`; `sandbox` is read-only and needs credentials, never use it for the standard cycle), `FEATURE_ACCESS_EQUIPMENT` and the other `FEATURE_*` flags.

Troubleshooting order: Docker running, then port 5432 and 3000 free, then `.env` has no space after `=` (the loader refuses it), then database missing a migration (reset), then `code/logs/web.log`.

Never point the app at a client production environment or a real JobDiva. The demo starts with **New email** in the inbox view.
