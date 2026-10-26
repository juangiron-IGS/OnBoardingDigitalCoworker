# Demo script (live demo and backup video)

Length: about 7 minutes. All data is synthetic, and every person, company and ID is invented.

## Before you start

From `code/` in Git Bash:

```bash
./scripts/reset.sh     # empty demo database, seed rules and emails
./scripts/start.sh     # starts the web app and runs the health check
```

Open http://127.0.0.1:3000. The health line should read `web app: ok · database: ok · JobDiva: mock · model: rules`.

## 1. The problem in one sentence (20 s)

> "Starts arrive from JobDiva with the most useful fields blank, so onboarding chases data by email. The Coworker checks the start the moment it arrives, and nothing reaches a system without a human approval."

## 2. A start with missing data (J1) (1 min 30 s)

1. Select **Recruiter** at the top right.
2. Go to **Simulated inbox** and press **Simulate arrival** on *New start - SYN-0043 - QA Engineer*.
3. Point out the yellow banner: *Needs clarification*. Two fields are missing.
4. Open **Simulated alerts**. The alert names the exact fields (*Bill rate*, *Timesheet approver*), not a generic "data incomplete".

## 3. The recruiter answers in the chat (1 min)

1. Go to **Chat** and pick *SYN-0043* on the left.
2. The Coworker asks one question at a time. Answer `61.00 USD/h`, then `Lee Example`.
3. The Coworker replies that the case is complete and package v1 is ready for the approver.

> "It asks only for what is missing, once."

## 4. Status in the chat (30 s)

Type `How is SYN-0043 doing?`. The reply gives the state and who must act, from the record only.

## 5. Approval (J2) and restricted data (1 min 30 s)

1. Select **IT** and open **Approval**. FLSA and sponsorship show *Restricted*.
2. Select **Approver (Consultant Onboarding Supervisor)**. The values are now visible.
3. Point out that every line shows its label (source, recommended, exception) and its source or rule, for example **R-PA-02** (*CA state withholding form, DE 4*).
4. Press **Approve v1**. The JobDiva and Workflow agent creates 2 simulated records.

## 6. Status and audit (1 min)

Open **Status**:
- the case path from *Received* to *Actions executed*;
- the JobDiva case (mock) and the task list, each carrying the **approval ID**;
- the audit log: Intake and Validation, Policy and Case Setup, the approver and JobDiva and Workflow on one case, with the rules used.

> "Three specialized agents on one case, coordinated by the Orchestrator. Every action is in the audit log."

## 7. Guardrails (1 min)

1. **Duplicate:** in the inbox, simulate *SYN-0042 - Data Analyst*, then *Start confirmation - SYN-0042*. The second one is blocked and names the existing case.
2. **FLSA conflict:** simulate *SYN-0045* (`05_flsa_conflict`). The start email says Non-exempt and JobDiva says Exempt. The Coworker selects no value, escalates to the Onboarding Team and HR, and the package is **blocked**: *Approve* stays disabled.
3. **Already in JobDiva:** in the chat, send `Candidate ID: SYN-0040` and `Start date: 2026-11-02` on two lines. It is blocked: that person is already onboarding in JobDiva.

## 8. Close (20 s)

> "Human approval before any action, no legal decisions, synthetic data only, and the JobDiva connector only reads. The rules are data the business owns, and a model engine plugs in without changing the agents."

## If something fails live

- Run `./scripts/reset.sh` and then `./scripts/start.sh`, and resume from the step you were on.
- If it still fails, play the backup video.
