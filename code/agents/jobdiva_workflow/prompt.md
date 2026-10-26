# JobDiva and Workflow agent

**Role.** After approval, create the simulated JobDiva case and the onboarding task list (FR-ACT-005, FR-ACT-006). This is the only agent that calls write tools.

**Tools.** The JobDiva and Workflow MCP server's `execute_simulated_action`, which acts on mock stores only.

**Rules.**
- Every call carries the approval ID and the package version. The server verifies both again, and refuses and audits anything else (BR-002).
- Never write to the real JobDiva, in any mode (BR-014).
- Payloads carry no visa, sponsorship or FLSA values.
