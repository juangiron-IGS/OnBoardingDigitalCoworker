# Architecture as implemented

The design is SAD v1.2, Alternative B. This page shows what runs in the demo on October 28, 2026, and where it still differs from the target.

```mermaid
flowchart LR
    Browser["Browser: 5 views<br/>inbox · chat · approval · alerts · status<br/>role selector"]

    subgraph Web["Web app (FastAPI) on 127.0.0.1:3000"]
        API["API<br/>X-Role · 400 / 403 / 409"]
        subgraph Agents["Onboarding Coworker"]
            Orch["Onboarding Orchestrator<br/>+ chat channel"]
            Intake["Intake and Validation"]
            Policy["Policy and Case Setup"]
            WF["JobDiva and Workflow"]
            Access["Access and Equipment (Should)<br/>FEATURE_ACCESS_EQUIPMENT"]
            Know["Onboarding Knowledge (Should)<br/>cites the record · drafts labelled"]
            Model["Model client<br/>engine: rules (no model)<br/>usage meter"]
        end
        Case["Case service<br/>states · approval gate · audit · privacy"]
        Rules[("Rules catalog<br/>YAML: paperwork, path, kit,<br/>owner, overhead, intake labels,<br/>knowledge records")]
        Mail["Outlook mock<br/>synthetic .eml"]
        Client["MCP client<br/>refusals keep their reason"]
    end

    DB[("PostgreSQL 16 (Docker)<br/>cases · package versions · approvals<br/>audit_log (insert-only) · action_ledger<br/>mocks: jobdiva_cases · task_lists · alerts")]

    subgraph MCP["MCP servers (one process each, streamable HTTP on 127.0.0.1)"]
        S1["jobdiva-read :8101<br/>mock or read-only sandbox<br/>no write tools"]
        S2["jobdiva-workflow :8106<br/>single writer: re-verifies<br/>approval + version"]
        S3["teams-mock :8108<br/>alerts"]
    end

    Browser --> API --> Orch
    Orch --> Intake --> Model
    Orch --> Policy --> Rules
    Orch --> Access --> Rules
    Orch --> Know --> Rules
    Orch --> Case
    WF --> Client
    Orch --> WF
    Orch --> Client
    Client -- MCP --> S1
    Client -- MCP --> S2
    Client -- MCP --> S3
    API --> Mail
    Case --> DB
    S2 --> DB
    S3 --> DB
```

`AGENT_TRANSPORT=mcp` (the default in `.env.example`) runs the layout above: `start.sh` starts the three MCP servers before the web app, and the health check waits until each one answers. `AGENT_TRANSPORT=in_process` is the fallback for the demo: the agents call the same services the servers wrap, behind the same interfaces, with the same governance code. The Outlook mock is read by the web app's inbox in both modes.

## Where it matches the design

| Control | How it is enforced | Test |
|---|---|---|
| Approval gate (BR-002) | Every action re-verifies the approval ID against the current package version, inside the action's transaction | `test_no_action_without_approval`, `test_version_mismatch_blocked` |
| Single writer | Only `jobdiva_workflow` registers a write tool; the test scans every MCP server | `test_only_workflow_agent_writes` |
| Never write to JobDiva (BR-014) | The JobDiva READ server has no write tools; the sandbox client refuses anything but GET | `test_jobdiva_read` |
| Append-only audit | No database role has UPDATE, DELETE or TRUNCATE on `audit_log`; decisions and applied actions are insert-only | `test_every_action_is_audited` |
| Restricted data (BR-011) | The case service hides visa, sponsorship and FLSA from recruiter and IT; alerts name fields, never values | `test_it_role_does_not_see_restricted_fields`, `test_escalation` |
| No legal decisions (BR-001) | FLSA and classification conflicts become exceptions, escalated to the Onboarding Team and HR, and the package is blocked | `test_escalation` |
| Rules are data | Paperwork, path, kit, owner, overhead and intake labels are YAML with rule ID, owner and version | `test_rule_lookup` |

## Where it differs, and why

| Topic | Target (SAD) | Demo | Reason |
|---|---|---|---|
| Model | A model reads free text | `claude` engine (Claude Haiku 5.5) reads free text when `MODEL_PROVIDER=claude`; `rules` stays the default and the fallback | Restricted fields never reach the model; every call is metered and capped (ADR-006, TC-004) |
| Velocity 2.0 | Agent runtime | Delivery method | Corrected in ADR-006 |
