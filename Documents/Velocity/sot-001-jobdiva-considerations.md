# SOT-001 JobDiva Considerations

**Project:** Onboarding Digital Coworker
**Applies to:** SOT-001 Source of Truth
**Date:** 2026-10-16
**Basis:** Onboarding Digital Coworker — Checkpoint Deliverable (October 14, 2026)

This document records the JobDiva facts that SOT-001 does not yet state. They affect the business rules (§5) and the JobDiva integration (§7, INT-001).

---

## 1. Single writer

Only the JobDiva and Workflow agent writes to systems (the JobDiva case, the IT and equipment requests, the task list and the payroll package). It writes only after approval, and only with an approval ID for the current package version. No other agent writes to any system.

## 2. No writes to the real JobDiva

The Coworker never writes to the real JobDiva, not even in the sandbox. All case creation and updates happen in the JobDiva mock.

## 3. Two connector modes

The agents always call the same JobDiva connector (an MCP server). It has two modes, selected by an environment variable:

| Mode | Default | What it does |
|---|---|---|
| Mock | Yes | Creates and updates the case with synthetic data. Used for the demo. |
| Sandbox | No | Read-only. Reads a test candidate's start, its start notes and the duplicate search. Enabled only if JobDiva API credentials (the account Client ID and a dedicated API user) are available. |

If the API credentials are not available, the demo runs on the mock only.

## 4. Token handling

The sandbox uses API authentication, not the web login. The API credentials return a token that is renewed when it expires. The token lives in memory only and is never written to the audit log or any other log. The credentials go in a local `.env` outside the repository; the repository ships only a `.env.example` with the variable names.
