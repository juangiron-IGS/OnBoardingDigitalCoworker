---
name: security-accessibility
description: Security and accessibility checks for the Coworker on localhost: secret scan (NFR-SEC-005), lint security rules, dependency audit, role-restriction tests, localhost binding, and the automated contrast check (NFR-USE-002). Use before a release, a pull request that touches security, or when a security or usability NFR case is run.
---

# Security and Accessibility (local)

Here everything runs on `127.0.0.1`: there is no staging and no production, so **no DAST and no external scan**. Never aim a tool at a host other than `127.0.0.1`.

Checks, each tied to its case:
- **Secrets (NFR-SEC-005):** use the `secret-scan` skill. Any finding blocks.
- **Code security rules:** `code/.venv/Scripts/python -m ruff check .` (includes the bandit-derived `S` rules). Any finding blocks.
- **Dependencies:** `pip install pip-audit` into the venv, then `code/.venv/Scripts/python -m pip_audit`. It is a local tool and is not added to `pyproject.toml` unless the team agrees. Critical or High advisories are reported; an unfixable one is a warning.
- **Role restrictions (NFR-SEC-002, BR-011):** pytest negative tests: IT cannot see FLSA, sponsorship or visa, and MCP tools cannot approve. They run with the rest of the suite.
- **Localhost binding (NFR-SEC-001):** `docker compose ps` shows `127.0.0.1:5432`, and a listening-port check shows the web and MCP ports bound to `127.0.0.1` only.
- **Contrast (NFR-USE-002):** the automated check runs Playwright with axe-core against `http://127.0.0.1:3000` on the views (dashboard, inbox, approval, alerts, status, knowledge). A WCAG 2.1 AA contrast failure is a defect. Keyboard use is a manual case.
- Verdict words: `fail` (a blocking finding), `advisory_only`, `pass`. Save evidence under `code/tests/evidence/`.
