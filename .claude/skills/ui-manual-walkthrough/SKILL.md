---
name: ui-manual-walkthrough
description: Running the manual UI test cases of the Coworker (inbox, chat panel, approval, alerts, status, knowledge views) with the Playwright MCP browser, capturing evidence and recording pass or fail per case. Use for the demo scenario, the acceptance criteria AC1 to AC12, and the cases the plan marks as manual.
---

# Manual UI walkthrough

Tool: the Playwright MCP tools (`mcp__playwright__*`, already allowed in `.claude/settings.json`). Load them with ToolSearch first. The app must be running (`run-coworker-locally`) with `MODEL_PROVIDER=rules` unless the case says otherwise. Functional UI checks are manual by plan (QTOOL-002); do not write a Playwright test framework for them.

Procedure:
1. Choose the cases: the Test Cases document, §23.5 (demo scenario steps) and §23.6 (AC1 to AC12), plus the cases whose Code State says manual. Start from a clean database (`test-data`: `./scripts/reset.sh`, after telling the user).
2. Follow the case steps literally on http://127.0.0.1:3000. Switch roles with the app's role selector (recruiter, onboarding team, approver, IT). Use `browser_snapshot` to read the page state, not screenshots alone.
3. For each expected result, state what was seen. Take a screenshot for each case and save it under `code/tests/evidence/ui/<case-id>-<step>.png` (synthetic data only; check that no key appears).
4. Record: case ID, build (short commit), settings, tester, result (pass, fail, blocked), evidence path. A step the app cannot perform is **blocked** with the product gap from §23.7, not a pass and not silently skipped.
5. Failures go to `bug-reporting`. Do not fix product code.

Checks to include on every view: no console errors (`browser_console_messages`), no failed network calls (`browser_network_requests`), restricted fields (FLSA, visa, sponsorship) hidden from the IT role, and the approval buttons disabled for roles that cannot approve.

Report results to the user in plain language: how many cases passed, failed and were blocked, with the evidence folder.
