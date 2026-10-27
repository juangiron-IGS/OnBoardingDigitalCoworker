---
name: ci-github-actions
description: Creating and maintaining the GitHub Actions workflow that runs pytest and ruff on every pull request (QUAL-008, QTOOL-006, entry criterion CRIT-017). Use when .github/workflows/ci.yml must be written or fixed, or when a CI run fails.
---

# CI with GitHub Actions

Today `.github/workflows/ci.yml` **does not exist**; the gate is run locally as the fallback. The workflow is test infrastructure, so QA may write it, but it must not change product code. Open it as a pull request from a `feature/ci` or `docs/...` branch.

Content the workflow needs (from `scripts/apply_db.sh` and `tests/conftest.py`):
- Trigger: `pull_request` and `push` to `main`.
- Python: set `python-version` to 3.12 or later (the repo requires `>=3.12`).
- A PostgreSQL 16 service with `POSTGRES_PASSWORD` from a CI secret or a throwaway value (it is not a real secret, but do not reuse the local one). Expose `127.0.0.1:5432`.
- Install: `pip install -e ".[dev]"` from `code/`.
- Database setup: `psql` is on the runner, so `apply_db.sh` uses it directly. Export `DB_PORT`, `DB_NAME`, `DB_ADMIN_PASSWORD`, `DB_APP_PASSWORD`, `DB_AUDIT_PASSWORD`, create `${DB_NAME}_test`, run `apply_db.sh` for both databases, and set `DATABASE_URL` and `AUDIT_DATABASE_URL`.
- Steps: `ruff check .`, `ruff format --check .`, `pytest --cov=. --cov-report=term` (the conftest forces mock, rules and in-process, so no secrets or model key are needed), then the secret scan (`secret-scan`), then upload `tests/evidence`-style outputs as an artifact.
- Gates: pytest, ruff and the secret scan must pass; a coverage threshold only if the team set one (the Test Plan assumes 70%; recorded runs show 94% to 96%).
- Never print or echo secrets, never use the `claude` engine or the JobDiva sandbox in CI.

After writing it, check the YAML locally (`python -c "import yaml; yaml.safe_load(open('...'))"`). A CI result is claimed only after the run has actually happened on GitHub. Update the Test Plan/QSOT statements about CRIT-017 and QTOOL-006 through `test-cases-maintenance`.
