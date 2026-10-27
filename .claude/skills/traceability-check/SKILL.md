---
name: traceability-check
description: Verifying that the test cases claimed as covering a requirement (FR, NFR, AC, BR) resolve to real pytest tests in code/tests. Use before reporting coverage, after the Test Cases document or the tests change, or when asked "what is really covered".
allowed-tools: Read, Glob, Grep
---

# Traceability Check (Test Cases to pytest)

Three layers:

- **L1, requirements:** the Velocity documents (`Documents/Velocity/`): FRS (FR, UC, BR), NFR register, Backlog (US, AC). Input, never rewritten.
- **L2, claimed coverage:** `Documents/Velocity/04. Quality/03. Onboarding Digital Coworker_test-cases.md`. Each case `QC-[MODULE]-[P|N|E]-[NNN]` has a **Code State** (executable, partly executable, pending) and an **Automated by** field naming tests. The matrices are §23.1 to §23.11.
- **L3, actual coverage:** `code/tests/**/test_*.py` (`def test_...`, including parametrised ids). Manual and scripted-performance cases have no pytest test by design.

How to apply:
- For each name in "Automated by", Grep `def <name>` under `code/tests/`. Existence is not execution: report "found", never "passing". Pass or fail comes from `code/tests/evidence/pytest-results.txt` or a fresh run.
- Classify each discrepancy as exactly one of `orphan-id` (case or requirement ID missing in the other layer), `unmapped` (requirement with no case), `drift` (test name or Code State differs from the code, for example a "pending" case whose test now exists, or an "executable" case whose test was renamed) and `stale-file` (test with no case).
- Compare the counts with the Test Plan and §23.4 (cases by state) and report differences.
- Clean means say "clean" and show nothing. Gaps: one table, `drift` and `unmapped` first. This skill only reports; the Test Cases document is edited by `test-cases-maintenance`.
