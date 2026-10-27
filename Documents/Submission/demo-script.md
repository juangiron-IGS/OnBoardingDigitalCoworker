# Demo script (live demo and backup video)

Length: about 7 minutes. All data is synthetic, and every person, company and ID is invented.

## Before you start

From `code/` in Git Bash:

```bash
./scripts/reset.sh     # empty demo database, seed rules and emails
./scripts/start.sh     # starts the MCP servers and the web app, then runs the health check
```

Open http://127.0.0.1:3000. The health line should read `web app: ok · database: ok · transport: mcp · JobDiva: mock · model: rules · MCP: jobdiva-read ok, jobdiva-workflow ok, teams-mock ok, knowledge-mock ok, onboarding-coworker ok`. Check that `code/.env` has `AGENT_TRANSPORT=mcp`, `JOBDIVA_MODE=mock` and `FEATURE_ACCESS_EQUIPMENT=true`.

## 1. The problem in one sentence (20 s)

> "Starts arrive from JobDiva with the most useful fields blank, so onboarding chases data by email. The Coworker checks the start the moment it arrives, and nothing reaches a system without a human approval."

## 2. A start with missing data (J1) (1 min 30 s)

1. Select **Recruiter** at the top right.
2. In **Simulated inbox**, press **New email**. The compose window is filled with a sample start (note its candidate ID, for example *SYN-0873*); press **Send**.
3. The email lands in the onboarding mailbox and the Coworker processes it at once. Point out the yellow banner: *Needs clarification*. Two fields are missing.
4. The chat button at the bottom right shows a red badge: the alert to the Recruiter names the exact fields (*Bill rate*, *Timesheet approver*), not a generic "data incomplete".

   *Backup:* press **Simulate arrival** on *New start - SYN-0043 - QA Engineer* instead, and use SYN-0043 below.

## 3. The recruiter answers in the chat (1 min)

1. Open the chat (button at the bottom right). The alert is in the conversation; press **Open this case**.
2. The Coworker asks one question at a time, like a Teams chat. Press Enter to send. Answer `61.00 USD/h`, then `Lee Example`.
3. The Coworker replies that the case is complete and package v1 is ready for the approver.

> "It asks only for what is missing, once."

## 4. Status in the chat (30 s)

Type `How is <candidate ID> doing?`, for example `How is SYN-0873 doing?`. The reply gives the state and who must act, from the record only.

## 5. Approval (J2) and restricted data (1 min 30 s)

1. Select **IT** and open **Approval**. FLSA and sponsorship show *Restricted*.
2. Point out the Access and Equipment lines: the Chelsea Tech laptop request (**R-AC-01**), 2% overhead for INSPYR equipment (**R-OH-01**) and the bill-back rule (**R-BB-01**). Press **Approve request for v1**.
3. Select **Approver (Consultant Onboarding Supervisor)**. The restricted values are now visible.
4. Point out that every line shows its label (source, recommended, exception) and its source or rule, for example **R-PA-02** (*CA state withholding form, DE 4*).
5. Under **Follow-up owner**, the Coworker only recommends (**R-OW-01**). Type another name and press **Assign owner**: the assignment replaces the recommendation and is audited.
6. Press **Approve v1**. The JobDiva and Workflow agent creates 3 simulated records: the JobDiva case, the task list and the Chelsea Tech request, which goes out only because IT and the approver both approved v1.

## 6. Status and audit (1 min)

Open **Status**:
- the case path from *Received* to *Actions executed*;
- the JobDiva case (mock) and the task list, each carrying the **approval ID**;
- the audit log: Intake and Validation, Policy and Case Setup, the approver and JobDiva and Workflow on one case, with the rules used.

> "Three specialized agents on one case, coordinated by the Orchestrator. Every action is in the audit log."

## 7. Guardrails (1 min)

1. **Duplicate:** in the inbox, simulate *SYN-0042 - Data Analyst*, then *Start confirmation - SYN-0042*. The second one is blocked and names the existing case.
2. **FLSA conflict:** simulate *SYN-0045* (`05_flsa_conflict`). The start email says Non-exempt and JobDiva says Exempt. The Coworker selects no value, escalates to the Onboarding Team and HR, and the package is **blocked**: *Approve* stays disabled. Then select **Onboarding Team**, choose HR's answer under **Escalated to HR** and press **Record HR's answer**: the package is rebuilt as v2, the FLSA line cites **HR**, and v2 can be approved.
3. **Already in JobDiva:** in the chat, send `Candidate ID: SYN-0040` and `Start date: 2026-11-02` on two lines. It is blocked: that person is already onboarding in JobDiva.

## 8. Onboarding knowledge (1 min)

1. Select **Onboarding Team** and open **Knowledge**. Ask *Which forms does a hire in Philadelphia need?*: the answer cites **KB-005** and says it is an *unvalidated draft*.
2. Press **Validate** on KB-005 and ask again: the same answer is now *Validated by the Onboarding Team*.
3. Ask *Which forms does a hire in Ohio need?*: the Coworker has no validated answer and the question appears under **Pending for the Onboarding Team**.
4. In the chat panel, ask *How do I request a laptop for my new hire?*: the Onboarding Knowledge agent answers from **KB-003**. A question about FLSA or classification is never answered: it is logged for HR without keeping the text.

## 9. Close (20 s)

> "Human approval before any action, no legal decisions, synthetic data only, and the JobDiva connector only reads. The rules are data the business owns, and a model engine plugs in without changing the agents."

## If something fails live

- Run `./scripts/reset.sh` and then `./scripts/start.sh`, and resume from the step you were on.
- If an MCP server will not start, set `AGENT_TRANSPORT=in_process` in `code/.env`, run `./scripts/stop.sh` and `./scripts/start.sh`. The agents then call the same services directly, with the same controls.
- If it still fails, play the backup video.
