# Onboarding Digital Coworker

A multi-agent Digital Coworker for INSPYR that turns a new-hire notification into a complete, validated and approved onboarding case. **It chases the information, reminds and prepares; people decide and approve.**

Built for the INSPYR *Movers n’ Shakers* hackathon (October 2026) on **Velocity 2.0**. Business owner: **Tonya Ramirez**, Consultant Onboarding Supervisor.

> **Status:** design and scope approved at the October 14 checkpoint. Implementation is in progress; sections marked *planned* describe the target setup and will be completed as the code lands.

| Milestone | Date | Status |
| --- | --- | --- |
| Checkpoint: design and scope | October 14, 2026 | Delivered: [checkpoint deliverable](Documents/CheckPoint/14October/checkpoint-deliverable.md) |
| Foundations: Velocity 2.0, data, mocks | October 15–16 | In progress |
| Journeys J1 and J2 (Must) | October 17–20 | Planned |
| Tests, README, presentation, video | October 21–22 | Planned |
| Final submission | October 22, 2026 | Planned |

## Business problem and expected outcome

When a recruiter submits a start in JobDiva, the most useful fields (work location, FLSA, billing contact, timesheet approver, equipment, sponsorship and visa) are optional. They often arrive blank, so the onboarding team chases data by email, picks paperwork from memory and reconciles payroll reports by hand.

The Coworker moves validation to the start: nothing reaches onboarding incomplete, and nothing reaches a system without human approval.

| Metric | Baseline | Target |
| --- | --- | --- |
| Document onboarding (receipt to documents complete) | ~3 days | 1 to 1.5 days (pilot) |
| Cases reaching onboarding with missing data and no alert | Frequent | 0 |
| Time from the last answer to a package ready for approval | Not applicable | 5 minutes or less |
| Actions executed without human approval | Not applicable | 0 |

## Digital Coworker responsibilities

| The Coworker | People |
| --- | --- |
| Reads the start email or chat and detects missing or inconsistent data | The recruiter corrects the flagged fields |
| Recommends path, paperwork, owner, access and equipment, citing the rule | The Onboarding Team confirms the case and resolves escalations |
| Builds an approval package with the source of every data point | Tonya Ramirez approves, returns or rejects the package |
| Creates the JobDiva case and requests (simulated) only after approval, and keeps JobDiva updated | IT approves laptops; LDC approves the welcome kit and feedback |
| Logs every action for audit | The business maintains the rules and validates new knowledge |

The Coworker never decides worker classification, compensation or legal employment questions; unclear cases are escalated to the Onboarding Team.

**MVP scope (Must):** intake by email or chat, adaptive questions, validation of the 7 recruiter-note fields, rule-based path and paperwork, onboarding owner, approval package, approval gate, simulated actions with JobDiva kept current, duplicate prevention and audit log. Should and Could items are listed in the [checkpoint deliverable](Documents/CheckPoint/14October/checkpoint-deliverable.md#2-prioritized-capabilities-and-responsibilities).

## Agent architecture and orchestration

To users it is one Coworker. Inside, an Onboarding Orchestrator owns the case and splits the work across specialized agents that share one context. Only the JobDiva and Workflow agent writes to systems, and only with an approval ID for the current package version.

![Agent architecture](Documents/CheckPoint/14October/images/08-architecture.png)

| Agent | Priority | Responsibility |
| --- | --- | --- |
| Onboarding Orchestrator | Must | Case state, routing, timing, escalations, approval package and approval gate |
| Intake and Validation | Must | Extracts fields from email or chat, checks completeness and consistency, detects duplicates |
| Policy and Case Setup | Must | Rule engine: path, FLSA agreement, state, city and client forms, onboarding owner |
| JobDiva and Workflow | Must | After approval, creates and updates the JobDiva case, requests, task list and payroll package |
| Access and Equipment | Should | Email, Teams, apps, laptop, 2% or 5% overhead and bill-back |
| Candidate Follow-up | Should | Checklist, tiered reminders and document verification |
| Onboarding Knowledge | Should | Answers process questions from validated records; proposes drafts for human validation |
| Culture and Belonging (IGS) | Could | LDC tracker, welcome kit and two-month feedback |

Case lifecycle and the demo sequence are documented in [section 5 of the checkpoint deliverable](Documents/CheckPoint/14October/checkpoint-deliverable.md#5-solution-design).

## Prerequisites and installation

*Planned.* The solution runs as a local demo:

- Access to **Velocity 2.0** with the team’s license
- A local web app (the Coworker’s chat and approval screens) connected to the orchestrator on Velocity 2.0
- Simulated services (MCP servers) for JobDiva, IT and equipment, payroll, email and Teams, and the LDC tracker
- Python 3 for the helper scripts in `tools/` (`python-docx` for `docx_to_md.py`)

Step-by-step installation commands will be added with the source code.

## Configuration

All configuration comes from environment variables. The repository will ship a `.env.example` with variable names only; real values go in a local `.env`, which is git-ignored.

| Variable | Purpose |
| --- | --- |
| `JOBDIVA_MODE` | `mock` (default) or `sandbox` (read-only) |
| `JOBDIVA_BASE_URL` | JobDiva API base URL (sandbox mode only) |
| `JOBDIVA_CLIENT_ID` | Account Client ID issued by JobDiva support (sandbox mode only) |
| `JOBDIVA_API_USER` | Dedicated API user (sandbox mode only) |
| `JOBDIVA_API_PASSWORD` | API user password (sandbox mode only) |

Velocity 2.0 and model settings will be added to the same file.

## How to run the solution

*Planned.* Start the simulated services, the orchestrator on Velocity 2.0 and the local web app, then open the chat view. Exact commands will be added with the source code.

## How to run the demonstration

*Planned.* The demo uses synthetic data only:

1. A start email arrives for a W-2 consultant in Philadelphia with the timesheet approver blank and a contradictory work arrangement.
2. The Coworker alerts the recruiter with the two exact fields; the recruiter answers in the chat.
3. The Coworker recommends the paperwork, the owner and, if available, access and an INSPYR laptop with 2% overhead.
4. The Consultant Onboarding Supervisor assigns the follow-up owner, who reviews the package with sources.
5. The Onboarding Team asks the Coworker for the status of their candidates in the chat.
6. After approval (and IT approval for the laptop), the Coworker creates the case in the JobDiva mock, the requests and the task list.
7. A second attempt with the same person and date is blocked as a duplicate.

A backup demo video will be added before the final submission.

## Security and governance considerations

- **Human in the loop:** every action on a system, access, equipment or purchase needs explicit approval of the current package version.
- **No legal decisions:** FLSA, classification and compensation come from the field or HR; conflicts are escalated.
- **Traceability:** every package line is labeled (source, inferred, recommended, exception) and every agent action is in the audit log.
- **Data:** synthetic data only; no connection to client production environments. Visa, sponsorship and FLSA are restricted by role.
- **Secrets:** no credentials in the repository; the JobDiva token lives in memory and is never logged.
- **JobDiva:** the Coworker never writes to JobDiva, not even in the sandbox.
- **Duplicates:** a request or case with the same person and start date is blocked.
- **Cost:** model usage stays within the assigned budget and is logged per run.

## Known limitations

- All enterprise systems (JobDiva, IT and equipment, payroll, email, Teams, LDC tracker) are simulated in the hackathon.
- JobDiva sandbox access depends on API credentials (Client ID and API user) that are not available yet; without them the demo runs on the mock only.
- Microsoft Teams integration is optional and depends on tenant permissions.
- Business rules (forms by state and city, overhead, bill-back) are seed data still being validated with the onboarding team.
- The scope covers the request through approval and its actions; background checks, I-9, payroll processing and real e-signature are out of scope.

## Reusable components

- **JobDiva connector** with mock and read-only sandbox modes behind one interface
- **Rules catalog as data** (path, paperwork, owner, overhead) maintained by the business
- **Approval package and approval gate** pattern with labeled, sourced data points
- **Onboarding knowledge module** with human validation before publishing
- **Audit log** schema for agent actions, data and rules used

## Repository structure

```
.
├── Documents/
│   ├── CheckPoint/14October/    Checkpoint deliverable (md, pdf, docx, pptx, images)
│   ├── HackatonDocuments/       Hackathon requirements and evaluation criteria
│   └── Employee Onboarding Digital Coworker - Solution Intake.(md|docx)
├── tools/                       Helper scripts (docx_to_md.py)
└── CLAUDE.md                    Guidance for AI-assisted development in this repo
```

Planned additions for the final submission: Velocity configuration, application source, agent definitions and prompts, integration scripts, database schema and migrations, seed data, tests and evidence, final presentation and backup video.

## Team

Juan Giron, Laura Hernandez, David Valdez, Carlos Puerta, Viviana Gomez and Michael Erskin (US).

## License

To be defined before the final submission, together with the dependency list.
