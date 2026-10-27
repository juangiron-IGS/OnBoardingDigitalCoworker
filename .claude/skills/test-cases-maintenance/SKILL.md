---
name: test-cases-maintenance
description: Keeping the Quality documents (Test Plan and Test Cases in Documents/Velocity/04. Quality) in step with the code and the tests. Use after pytest results change, after a feature branch merges to main, when a case gets or loses its test, or when counts and traceability matrices must be refreshed.
---

# Test Cases and Test Plan maintenance

Files (edit only these two unless the user says otherwise): `Documents/Velocity/04. Quality/02. Onboarding Digital Coworker_test-plan.md` and `.../03. Onboarding Digital Coworker_test-cases.md`. The QSOT (`01.`) is not edited here. Velocity regenerates these documents from its Answers record, so tell the user that a manual edit is lost on regeneration unless it is also recorded there.

What changes when the code moves:
- A case's **Code State** (executable, partly executable, pending) and its **Automated by** list of real pytest names. Check each name with `traceability-check` before writing it.
- Conditional cases (Access and Equipment, Candidate Follow-up, Onboarding Knowledge) stop being conditional when their agent and feature flag exist on `main`. Re-read `code/.env.example` for flag defaults and fix the statement about them.
- Product gaps (§23.7) are closed only when a test proves it, not when the code seems to have changed.
- Counts: totals by state in the Test Plan, §2 summary table, §23.4 and §24 must agree. Recount with Grep over the case headings after every batch.
- Revision History: add one row (version, date, `[QA Lead] (AI Assisted)`, what changed) and bump **Version** in both files together.
- Matrices: §23.1 (requirement to cases with execution state), §23.2 (case to requirement), §23.9 to §23.11 (Backlog ACs, use cases, business rules). A new case is added to every matrix it belongs in.

Rules for edits:
- Keep the case template (§1.3) and the ID convention `QC-[MODULE]-[P|N|E]-[NNN]`; never reuse a retired ID.
- Write in English, plain and specific: facts the reader can check, no counts without a source.
- State what was read and what was run: "read" and "passes" are different claims. The recorded evidence is cited with its date and commit.
- Before a large edit, copy the file to the scratchpad. The IDE can overwrite a file from a stale buffer: ask the user to close the open tab without saving, and re-read the file after editing.
- Work on a `docs/...` branch and open a pull request; do not commit to `main`.
