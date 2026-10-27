---
name: bug-reporting
description: Writing and proposing defect reports for the Onboarding Digital Coworker as GitHub Issues. Use when a test fails, the user found a defect while testing the app, or a product gap from Test Cases §23.7 must be filed. Produces a severity-classified report and waits for human approval before anything is filed.
---

# Bug Reporting (GitHub Issues)

Defects are tracked in **GitHub Issues** of `juangiron-IGS/OnBoardingDigitalCoworker` (QTOOL-004). There is no Azure DevOps here: ignore the `ado-*` scripts and `ado_organization`. Use the report layout below.

How to apply in this repo:
- Reproduce first, on a clean state (`./scripts/reset.sh` when data matters). Record the build (`git rev-parse --short HEAD`), `MODEL_PROVIDER`, `AGENT_TRANSPORT`, `JOBDIVA_MODE` and the feature flags, because they change behaviour.
- Link the failing case (`QC-XXX-Y-NNN`) and the requirement it checks (FR, NFR, AC, BR). A defect with no case is filed together with a proposed new case for the Test Cases document.
- Severity comes from the Test Plan defect classification (DEF-xxx) and Test Cases §23.7. A Must requirement that fails with no workaround is High. An action executed without an approval ID, FLSA/visa/sponsorship visible to the wrong role, or a production JobDiva URL accepted is Critical.
- Evidence: the failing pytest output, the audit-log rows for the case, or a screenshot. Synthetic data only; never paste a key, a token or a real person.
- Check open issues for a duplicate first (`gh issue list --search` if `gh` is installed, otherwise the Issues page).
- Present the draft in plain language and **wait for approval**. `gh` is not installed on this machine: hand over the title, labels and Markdown body, and the link `https://github.com/juangiron-IGS/OnBoardingDigitalCoworker/issues/new`. Never file without approval.
- Labels: `bug`, `severity:critical|high|medium|low`, and the module (`itk`, `val`, `rec`, `own`, `pkg`, `apr`, `act`, `aud`, `web`, `int`, `sec`, `perf`).
