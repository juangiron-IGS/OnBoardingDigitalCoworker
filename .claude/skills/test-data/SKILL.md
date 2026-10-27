---
name: test-data
description: Managing the data a Coworker test needs: the seed scenarios (TD-001 to TD-021), the test database, resets and isolation. Use when a test or a manual run needs a known starting state, when a result depends on data, or when reproducing a failure's data state.
---

# Test Data

Project facts:

- **Synthetic only.** Seed data lives in `code/db/seed/` (`mailbox/*.eml` start emails, `jobdiva/starts.json` JobDiva starts) and rules in `code/rules/`. No real person, client or key, ever (hard constraint).
- **Two databases.** The app uses `coworker`; pytest uses `coworker_test`. `tests/conftest.py` switches `DATABASE_URL` to `<DB_NAME>_test` and forces `MODEL_PROVIDER=rules`, `JOBDIVA_MODE=mock`, `AGENT_TRANSPORT=in_process` and the Should features off. Never point a test at the dev database.
- **Isolation in pytest.** Use the `app_conn` and `audit_writer_conn` fixtures: each test runs in a transaction that is rolled back. Build ids with the `case_id` fixture or `uuid4`. Tests that need PostgreSQL carry `pytestmark = pytest.mark.db`.
- **Full reset for manual and demo runs.** `./scripts/reset.sh` recreates the volume, migrations, roles and seeds for both databases. It destroys the local data: say so before running it. A database created before a new migration reached `main` lacks its tables, so reset after any `git pull` that adds `db/migrations/*.sql`.
- **Test Cases §22** defines TD-001 to TD-021. A scenario the seed does not hold yet (for example the onboarding team's W-2 in Philadelphia with two gaps, TD-018) is added as a new `.eml` in `code/db/seed/mailbox/` with its rule; do not alter a seed that other cases rely on, and note the new data in the Test Cases document.
- Cleanup always runs. A manual walkthrough that mutates the dev database ends with `./scripts/reset.sh` when the next run must start clean.
