# Measured metrics

Run: `WRITE_METRICS=1 .venv/Scripts/python -m pytest tests/e2e/test_measured_metrics.py` from `code/` (rules engine, test database, synthetic seed emails).

| Seed email | Result | Time to package ready | Questions asked | Fields missing or in conflict |
| --- | --- | --- | --- | --- |
| 01_complete_and_consistent | ready_for_review, package ready | 94 ms | none | none |
| 02_missing_two_fields | ready_for_review, package ready | 112 ms | Bill rate, Timesheet approver | Bill rate, Timesheet approver |
| 03_duplicate | blocked_duplicate | no package | none | none |
| 04_work_arrangement_contradiction | ready_for_review, package ready | 158 ms | Work arrangement | Work arrangement |
| 05_flsa_conflict | ready_for_review, package blocked | 123 ms | none | none |

- Simulated records after approval: 2, all with an approval ID.
- Workflow actions completed without an approval ID: 0.
- Approving the blocked FLSA package: refused (HTTP 409).
