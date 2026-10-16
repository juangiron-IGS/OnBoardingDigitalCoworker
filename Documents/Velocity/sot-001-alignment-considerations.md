# SOT-001 Alignment Considerations

**Project:** Onboarding Digital Coworker
**Applies to:** SOT-001 Source of Truth, version 1.0
**Date:** 2026-10-16
**Basis:** Onboarding Digital Coworker — Checkpoint Deliverable (October 14, 2026)

This document records the facts that SOT-001 v1.0 is missing or states differently from the approved checkpoint. SOT-001 should be updated to version 1.1 to reflect them. Existing IDs stay as they are; new entries are added after the last existing number.

---

## 1. Solution design

- **Platform.** Velocity 2.0 is the mandatory platform: agent runtime, orchestration and models. The hackathon demo runs locally with simulated services.
- **Channel.** To users there is one Coworker, reached through a lightweight local web app. It is the only mandatory channel, because Velocity 2.0 has no chat interface of its own. The app has five views:
  - Chat: conversational intake and status questions (recruiter and Onboarding Team).
  - Simulated email inbox: synthetic start emails, with a button that simulates a new one arriving.
  - Approval: the package with sources and the approve, return and reject actions.
  - Simulated alerts: the notifications that would go through Teams or email in production.
  - Status: the case in the JobDiva mock, the requests and the audit log.
- **Agents.** An Onboarding Orchestrator owns each case. It keeps the case state, decides which agent acts, manages timing and escalations, builds the package and enforces the approval gate. It routes work to specialized agents that share one context:

  | Agent | Priority | Responsibility |
  |---|---|---|
  | Intake and Validation | Must | Reads the email or chat, extracts fields, checks completeness and consistency, asks for what is missing, checks for duplicates |
  | Policy and Case Setup | Must | Applies the rules: path, agreement by FLSA, forms by state, city and client; recommends the owner; escalates unclear cases |
  | JobDiva and Workflow | Must | After approval, creates and updates the JobDiva case; creates requests, the task list and the payroll package |
  | Access and Equipment | Should | Recommends email, Teams, apps and equipment; computes overhead and bill-back; drafts the Chelsea Tech request |
  | Candidate Follow-up | Should | Sends the checklist, tiered reminders and correction requests; verifies what was delivered |
  | Onboarding Knowledge | Should | Answers process questions from validated records; proposes drafts; logs unresolved questions |
  | Culture and Belonging (IGS) | Could | LDC tracker entry, welcome kit, two-month feedback, congratulation draft |

  Notifications (email and Teams) are a shared tool with templates per audience, not an agent. The demo must show at least three specialized agents (Intake, Policy, JobDiva) collaborating on one case under the orchestrator.
- **Journeys.** J1 intake and validation (Must); J2 package, approval and actions (Must); J3 candidate follow-up, document verification and payroll package (Should); J4 cultural handoff to IGS with accelerated timing (Could).
- **Case states.** Received → Validated, or Needs clarification (back to Validated when answered) → Case set up → Ready for review → Approval gate → Approved, Rejected, or returned for correction (back to Validated) → Actions executed → Documents pending, In verification, Sent to payroll (Should) → Handoff to IGS (Could) → Closed. A duplicate is blocked at Received. JobDiva is updated at each state.
- **Single writer.** Only the JobDiva and Workflow agent writes to the simulated systems, and only with an approval ID for the current package version.

## 2. People and decisions

- **Tonya Ramirez**, Consultant Onboarding Supervisor and business owner, is notified of each new hire, assigns the follow-up owner, and approves, returns or rejects the onboarding package.
- **Onboarding Team** reviews and confirms the prefilled case, recommended path and owner before approval. It receives process escalations, including FLSA and classification conflicts. It asks the Coworker for the status of its candidates in chat, approves the payroll handoff, countersigns document verification and validates knowledge.
- **IT** approves the laptop together with the package, before any equipment action. It does not approve after the package.
- **Project team:** Juan Carlos Giron (Product Owner / BSA), Viviana Gomez, Laura Hernandez, David Valdez, Carlos Puerta and Michael Erskin. Viviana Gomez is a team member, not an external contributor.

## 3. Capability details

- **Intake.** The source is the JobDiva start email or chat. The Coworker asks only what the onboarding path requires; it asks no questions outside the path.
- **The 7 recruiter-note fields:** work city and state (where the consultant works, not where the position is based); FLSA (exempt or non-exempt, set by the field or HR); billing contact; timesheet approver; equipment (hardware tier and provider: INSPYR at 2% overhead or Apple Direct at 5%); sponsorship and visa (current visa status if INSPYR sponsors); additional notes (optional).
- **Other mandatory data**, from JobDiva or chat: role, manager, start date, client, division, line of business, employment type (W-2, contractor or corp-to-corp) and vendor company, work arrangement (onsite, remote or hybrid), pay rate and bill rate. Email, applications and shipping address if applicable.
- **Consistency.** Work arrangement is asked in three places in JobDiva today; the Coworker keeps one confirmed answer that feeds every record. The alert to the recruiter names the exact field.
- **Path and paperwork.** Paths are W-2, contractor and corp-to-corp. The agreement depends on FLSA; forms depend on state, city and client. Each recommendation cites its rule ID.
- **Onboarding owner.** Recommended by client type and role. The Consultant Onboarding Supervisor assigns the follow-up owner.
- **Approval package.** Every line carries a label (source, inferred, recommended or exception) and its source or rule ID. Package status is ready, blocked or needs clarification. Open exceptions are visible before approval. The package is ready within 5 minutes of the last answer.
- **Approval gate.** Approval is tied to the current package version. A returned package goes back to validation and needs a new approval. A rejected case stops.
- **Duplicates and audit.** Duplicates (same person and start date) are searched for in the case store and in JobDiva. The audit log records the action, agent, case, date, and the data and rules used.
- **Status questions in chat (Must, new).** The Onboarding Team can ask the Coworker about its candidates ("how are my candidates doing?"). The orchestrator checks JobDiva and the case store and answers in chat.
- **Access and equipment.** Email, Teams and applications; laptop with hardware tier and provider; a drafted Chelsea Tech request; IT approves the laptop.
- **Candidate follow-up.** Checklist to a synthetic candidate; reminders at 24 h and 48 h, then escalation to the onboarding owner.
- **Document check.** Delivered documents are checked against the case checklist (required by client, location and contract). Onboarding countersigns. No legal validation.
- **Payroll.** The payroll package is sent after Onboarding approves the handoff. Payroll returns become tasks for the onboarding owner.
- **Knowledge.** Answers cite the source record. The agent proposes drafts marked as unvalidated until the right person for the case validates them. Unanswered questions are logged as pending. Records keep their version history.
- **IGS handoff.** The hire is logged in the LDC tracker and the welcome kit is assigned by contract type; LDC approves the kit.
- **Leader feedback.** Collected at two months, with a draft congratulation; LDC approves both.
- **Status dashboard.** Shows status, pending items and risks.
- **New-hire information package.** Company, client and role information; Onboarding reviews it.

## 4. Business rules

- FLSA, classification and compensation come from the field or HR. The Coworker only maps them to paperwork and escalates conflicts or unclear cases to the Onboarding Team. HR owns the legal answer.
- Only the JobDiva and Workflow agent writes to systems, and only with an approval ID for the current package version.
- The Coworker never writes to the real JobDiva, not even in the sandbox.
- Business rules are data maintained by the business (Onboarding, IT and LDC). Each rule has an owner and a version and is cited by ID.
- Work arrangement has one confirmed answer that feeds every record.
- Bill-back is a per-client rule. When the client has no rule, the package shows it as an exception.
- The onboarding owner is recommended by client type and role.
- Reminders have a configurable cadence and a send limit.
- Visa, sponsorship and FLSA never appear in messages to leaders or in mass communications.

## 5. Constraints

- Velocity 2.0 is mandatory.
- No credentials in the repository; a `.env.example` lists the variable names only.
- Model usage stays within the assigned budget and is logged per run.
- Microsoft Teams is optional and is added only after the demo is stable.

## 6. Integrations

- Every enterprise system is a mock exposed as a tool or MCP server.
- **JobDiva:** one connector with two modes. Mock is the default and creates and updates the case with synthetic data. Sandbox is read-only (start, start notes, duplicate search) and is enabled only if API credentials (Client ID and a dedicated API user) are available. The token is kept in memory and never logged. Used by Intake and Validation and by JobDiva and Workflow.
- **Onboarding mailbox:** Outlook; reads start emails and sends notifications; mock with synthetic emails.
- **Microsoft Teams:** alerts to owners, IT and LDC; optional chat channel.
- **Chelsea Tech:** access and laptop requests approved by IT; never real orders.
- **Paychex:** receives the payroll package and returns issues.
- **LDC tracker:** SharePoint list owned by the LDC team.
- **Knowledge base:** seed data.
- **Velocity 2.0** (agent runtime) and the **local web app** (user channel) are also part of the solution.

## 7. Assumptions and risks

- Velocity 2.0 licenses and JobDiva API credentials are pending confirmation as of October 16. Without credentials, the demo runs on the JobDiva mock only.
- Recruiter emails have no standard format; the agent tolerates variations and asks for confirmation.
- The rules catalog (forms by state and city, overhead, bill-back) is seed data still being validated with Tonya Ramirez's team.

| Risk | Mitigation |
|---|---|
| Eight days to build and test | Build J1 and J2 end to end first; Should and Could only with a stable demo |
| Velocity 2.0 learning curve or licenses | Confirm licenses; a minimal case working on day one |
| Tacit business rules | Validate the rules catalog with the onboarding team; cite rule IDs |
| Recruiter emails with no standard format | Tolerate variations and ask for confirmation; propose a template |
| Extraction errors affecting payroll or classification | Mandatory human validation; no autonomous decisions |
| Exposure of visa, sponsorship or FLSA | Role-based permissions and data minimization in messages |
| Too many reminders | Configurable cadence and a send limit |
| Model cost overrun | Small models for extraction; usage logged per run |
| Low adoption | Co-design with onboarding and LDC |
| Demo failure on presentation day | Preloaded scenarios and a backup video |
| JobDiva credentials not available | JobDiva mock as the default mode |

## 8. Corrections to SOT-001 v1.0

| Topic | v1.0 says | Correct statement |
|---|---|---|
| Follow-up owner | The Approver assigns it as part of approval | Tonya Ramirez is notified and assigns it; the Onboarding Team reviews; Tonya Ramirez approves |
| FLSA and classification | Questions go to HR | Conflicts escalate to the Onboarding Team; HR owns the legal answer |
| IT laptop approval | After the package | Together with the package |
| Onboarding owner criteria | Client, location and contract | Client type and role |
| Onboarding Team role | Confirms cases and resolves escalations only | Also reviews the package, asks status in chat, approves payroll handoff, countersigns documents, validates knowledge |
| OQ-001 and OQ-002 | Reference themselves | Reference §13 only |

## 9. Open questions

- Which roles may see visa, sponsorship and FLSA data.
- Which clients pay bill-back for equipment.
- Whether the committee confirms read-only use of the JobDiva sandbox.

## 10. Delivery plan

The team plans by dates, not by sprint velocity:

| Dates | Work |
|---|---|
| October 14 | Checkpoint (delivered) |
| October 15–16 | Foundations and mocks |
| October 17–20 | Journeys J1 and J2 (Must) |
| October 19–20 | Should items in parallel, only if the Must journeys are stable |
| October 21–22 | Tests, README and video |
| October 22 | Final submission |

October 16 is the cutoff: if Velocity 2.0, the database and the mocks are not ready, the extensions are dropped and all time goes to J1 and J2.
