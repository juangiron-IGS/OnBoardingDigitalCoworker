---
name: pytest-coworker-testing
description: Writing, running and fixing pytest tests for the Onboarding Digital Coworker (unit, connectors, governance, e2e) from a QC- test case. Use when a Test Cases entry is pending or partly executable and needs a test, when a pytest run fails, or when the suite must be run for evidence.
---

# pytest for the Coworker

Binding rules for the code under test: `.claude/rules/backend-python-coworker.md`. QA edits **tests and test-design documents only, never product code** (CLAUDE.md). A failing test that shows a product defect is reported with `bug-reporting`, not fixed in `code/`.

Layout (`code/tests/`): `unit/` (domain, rules, model client), `connectors/` (MCP servers, JobDiva modes), `governance/` (the negative tests of the controls: approval, single writer, returned package, duplicates, audit, escalation), `e2e/` (HTTP API and over MCP), `evidence/`.

Writing a test from a case:
1. Open the `QC-` case in `Documents/Velocity/04. Quality/03. Onboarding Digital Coworker_test-cases.md`: steps, test data (TD-xxx), expected result, source of the expected result. The expected result comes from the requirement, never from what the code currently returns.
2. Pick the folder by what is checked. Controls go in `governance/` and need a positive and a negative test.
3. Reuse fixtures: `app_conn` (rolled-back transaction), `audit_writer_conn`, `case_id`, and the `repo`, `audit`, `case_set_up` fixtures in `tests/governance/conftest.py`. Mark database tests `pytest.mark.db`.
4. Name the test for the behaviour (`test_returned_package_needs_new_approval`), one behaviour per test, Arrange-Act-Assert. Assert the outcome and the audit-log entry (agent, case, data, rules).
5. Add the test name to the case's "Automated by" and move its Code State, using `test-cases-maintenance`.

Running (from `code/`, venv Python 3.12 or later):
- Prerequisite: `./scripts/start.sh` (PostgreSQL), and a database that has every migration (`./scripts/reset.sh` after a pull that adds one).
- All: `.venv/Scripts/python -m pytest -q`. One file or test: `... -m pytest tests/governance/test_package_flow.py::test_name -q`. Coverage: `--cov=. --cov-report=term`. Lint: `.venv/Scripts/python -m ruff check . && .venv/Scripts/python -m ruff format --check .`
- The suite forces `MODEL_PROVIDER=rules`, `JOBDIVA_MODE=mock`, in-process transport and the Should features off, whatever `code/.env` says. A test that needs a flag turns it on itself.
- Evidence: save the output with its header (`# pytest — <UTC time> — commit <short sha> (<branch>)`) in `code/tests/evidence/` (`pytest-results.txt`, `coverage.txt`, `lint.txt`). Never claim a result that was not run in this session.

Failures: classify first as test defect, environment (database missing a migration, Docker down, stale `.env`) or product defect. Fix the first two; file the third. Do not weaken an assertion or delete a test to turn it green.
