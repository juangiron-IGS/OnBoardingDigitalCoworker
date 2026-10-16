# Onboarding Digital Coworker — Checkpoint Deliverable

October 14, 2026 · Juan Carlos Giron Salazar

> Exported from the live document: [Onboarding Digital Coworker — Checkpoint Deliverable](https://claude.ai/code/artifact/de6c0e87-62ae-4b3d-9bf5-8612d2ed2f42). This version has no images: the diagrams are written out as text and tables.

## Executive summary

The Onboarding Digital Coworker receives a new hire (through the JobDiva start email or chat), detects what is missing or inconsistent, builds the case with the right paperwork, access and equipment, and presents it for approval; only then does it run simulated actions and follow up. **The Coworker chases the information, reminds and prepares; people decide and approve.**

This document answers the seven points of the October 14 checkpoint. It combines the Solution Intake, the session with the onboarding team (Tonya Ramirez), the checkpoint proposed by Viviana Gomez and her comments, the agent brief and the knowledge module specification.

| # | Checkpoint point | One-line answer | Section |
| --- | --- | --- | --- |
| 1 | Profile, mission, users and outcome | An onboarding assistant for INSPYR that cuts document onboarding from ~3 days to 1–1.5 days | 1 |
| 2 | Capabilities and responsibilities | 9 Must, 5 Should and 4 Could, each with an owner agent and a human checkpoint | 2 |
| 3 | MVP scope | Intake, validation, package and approval with simulated actions; follow-up and the IGS handoff as extensions | 3 |
| 4 | Current and redesigned process | Validation moves from the end to the start; back-and-forth with the field disappears | 4 |
| 5 | Solution design | One Coworker for the user; inside, an orchestrator and seven specialized agents on Velocity 2.0 | 5 |
| 6 | Data, tools and integrations | Local web app; JobDiva, IT, equipment, payroll and email simulated; rules and knowledge as data | 6 |
| 7 | Governance, criteria, risks and plan | Seven human checkpoints, 12 acceptance criteria and submission on October 22 | 7 |

**Confirmed decisions:** business owner Tonya Ramirez; final submission on October 22; Tonya Ramirez, Consultant Onboarding Supervisor, approves the package; the IT team owns and approves equipment requests; the LDC team owns its tracker; the start email can be used in the sandbox; Teams is optional.

## 1. Digital Coworker profile

The Coworker is the single entry point to start an onboarding at INSPYR: it turns a new-hire notification into a complete, validated and approved case that each team can act on.

| Item | Definition |
| --- | --- |
| Name | Onboarding Digital Coworker |
| Mission | No team should have to chase information: the Coworker detects what is missing, asks the right person, reminds, validates and prepares; people decide and approve. |
| Reach | From the recruiting notification (or the manager’s request) to approval and the resulting actions; as an extension, the handoff to IGS cultural onboarding. |
| Business owner | Tonya Ramirez, Consultant Onboarding Supervisor, INSPYR onboarding team |
| Platform | Velocity 2.0, local demo with simulated services |
| Principle | No action on systems, access, equipment or purchases without explicit human approval |

### Users

Eight user types interact with the Coworker; the two primary ones start and process the onboarding. To all of them it is one Coworker, with several touchpoints: email, chat and notifications.

| User | Type | What they do with the Coworker |
| --- | --- | --- |
| Recruiter or hiring manager | Primary | Starts the case from the start email or chat; gets an alert naming the exact missing field |
| Onboarding Team (Tonya Ramirez and her team) | Primary | Gets prefilled, validated cases with a checklist; confirms the case and handles only the alerts; an owner is assigned by client type and role |
| Approver (Tonya Ramirez, Consultant Onboarding Supervisor) | Secondary | Approves the onboarding package |
| IT | Secondary | Approves the laptop and access |
| HR | Secondary | Owns legal and classification questions |
| Candidate | Secondary | Receives the checklist and reminders |
| Payroll | Secondary | Gets a validated package |
| LDC (IGS) | Secondary | Handles the welcome and feedback |

### Business outcome

The main goal is to shorten document onboarding and get complete data on the first submission.

| Metric | Baseline | Target | Measured in |
| --- | --- | --- | --- |
| Document onboarding time (receipt to documents complete) | ~3 days | 1 to 1.5 days | Pilot |
| Cases reaching onboarding with missing data and no alert | Frequent, not measured | 0 | Demo and pilot |
| Mandatory data complete in the test scenario | Not applicable | 100% | Demo |
| Time from the last answer to a package ready for approval | Not applicable | 5 minutes or less | Demo |
| Actions executed without approval | Not applicable | 0 | Demo |
| Payroll returns to onboarding | Not measured | Measurable reduction | Pilot |
| Business reviewer score | Not applicable | 4 out of 5 or higher | Demo |

## 2. Prioritized capabilities and responsibilities

The 9 Must capabilities make up the October 22 demo; the Should items are built if the Must items are stable, and the Could items stay as extensions or pilot work.

**Human control.** The Onboarding Team is the human control for path and paperwork, the package and the approval gate, and resolves process escalations; Tonya Ramirez, Consultant Onboarding Supervisor, approves the package.

| ID | Priority | Capability | Owner agent | Human control |
| --- | --- | --- | --- | --- |
| M1 | Must | Intake from the JobDiva start email or from chat | Intake and Validation | Not applicable |
| M2 | Must | Adaptive questions: only what the path requires | Intake and Validation | Not applicable |
| M3 | Must | Completeness and consistency check of the 7 note fields, with an alert to the recruiter naming the exact field | Intake and Validation | The recruiter corrects |
| M4 | Must | Path and paperwork: W-2, contractor or corp-to-corp; agreement by FLSA; forms by state, city and client | Policy and Case Setup | Onboarding Team |
| M5 | Must | Onboarding owner assignment by client type and role | Policy and Case Setup | The Consultant Onboarding Supervisor assigns |
| M6 | Must | Approval package with the source of each data point and a status: ready, blocked or needs clarification | Orchestrator | Onboarding Team |
| M7 | Must | Approval gate: approve, return or reject before any action | Orchestrator | Onboarding Team; the Consultant Onboarding Supervisor approves |
| M8 | Must | Simulated actions: JobDiva case updated at each stage, requests and task list | JobDiva and Workflow | Only with approval |
| M9 | Must | Duplicate prevention and audit log | Orchestrator | Not applicable |
| S1 | Should | Access and equipment: email, Teams, apps, laptop, provider, 2% or 5% overhead and bill-back | Access and Equipment | IT approves the laptop |
| S2 | Should | Candidate checklist and tiered reminders (24 h, 48 h, then escalation) | Candidate Follow-up | Onboarding handles escalations |
| S3 | Should | Check of delivered documents against the checklist | Candidate Follow-up | Onboarding countersigns |
| S4 | Should | Payroll package and payroll returns turned into tasks | JobDiva and Workflow | Onboarding approves the handoff |
| S5 | Should | Knowledge base: answer with sources, propose drafts and log unresolved questions | Knowledge | The right person for the case validates |
| C1 | Could | Handoff to IGS: LDC tracker entry and welcome kit by contract | Culture and Belonging | LDC approves the kit |
| C2 | Could | Leader feedback at two months and draft congratulation | Culture and Belonging | LDC approves the feedback |
| C3 | Could | Dashboard of status, pending items and risks | Orchestrator | Not applicable |
| C4 | Could | Company, client and role information package for the new hire | Culture and Belonging | Onboarding reviews |

### Who does what

| The Coworker | People |
| --- | --- |
| Detects missing or inconsistent data and asks | Confirm the prefilled case |
| Recommends path, paperwork, access and equipment, citing the rule | Resolve process escalations (Onboarding Team) |
| Builds the package and the checklist | Approve, return or reject the package |
| Sends reminders and escalates past thresholds | Approve the laptop (IT) and the payroll handoff |
| Runs simulated actions only with approval | Approve the welcome kit and feedback (LDC) |
| Logs every action for audit | Maintain business rules and validate knowledge |

## 3. Confirmed MVP scope

The MVP covers everything from a new hire’s arrival until the approved case produces its actions; candidate follow-up and the IGS handoff are extensions if time allows.

| Journey | Priority | What it shows |
| --- | --- | --- |
| J1. Intake and validation | Must | The Coworker reads the start email (or receives “I want to hire John Agnitsch starting October 1”), extracts the data, detects gaps and inconsistencies and asks only what is needed |
| J2. Package, approval and actions | Must | It builds the package with sources; the Onboarding Team reviews it and the Consultant Onboarding Supervisor approves, returns or rejects it; only then are the JobDiva case, the requests and the task list created (simulated), and JobDiva is updated at each stage |
| J3. Follow-up and handoff | Should | Checklist and reminders to a synthetic candidate, document verification and payroll package |
| J4. Cultural handoff to IGS | Could | LDC tracker entry, welcome kit and two-month feedback cycle with accelerated timing |

### Data the intake must collect

| Field | Rule | Source |
| --- | --- | --- |
| Work city and state | Mandatory; where the consultant works, not where the position is based | Recruiter note |
| FLSA | Mandatory; exempt or non-exempt (set by the field or HR, never by the Coworker) | Recruiter note |
| Billing contact | Mandatory | Recruiter note |
| Timesheet approver | Mandatory | Recruiter note |
| Equipment (hardware tier) | Mandatory; if equipment is needed, provider INSPYR (2% overhead) or Apple Direct (5%) | Recruiter note |
| Sponsorship and visa | Mandatory; if INSPYR sponsors, current visa status | Recruiter note |
| Additional notes | Optional; passed to onboarding or back office | Recruiter note |
| Role, manager, start date, client, division, line of business | Mandatory | JobDiva or chat |
| Employment type and vendor company | Mandatory; W-2, contractor or corp-to-corp | JobDiva or chat |
| Work arrangement (onsite, remote or hybrid) | Mandatory; one answer for every record | Chat |
| Pay rate and bill rate | Mandatory | JobDiva |
| Email, applications and shipping address | If applicable | Chat |

### In and out of scope

| In scope | Out of scope |
| --- | --- |
| Intake by email and chat with adaptive questions | Recruiting inside JobDiva before the notification |
| Validation of the 7 fields and consistency rules | Legal classification or compensation decisions |
| Rule engine: client, location and contract to documents, owner and kit | Background checks, drug screens, I-9 and E-Verify |
| Access, equipment, overhead and bill-back (Should) | Real equipment purchases or provisioning |
| Approval package and human gate | Payroll processes after the handoff |
| Simulated JobDiva, IT, equipment, payroll and email | Production JobDiva API and real data |
| Follow-up with a synthetic candidate (Should) | Real e-signature and legal validation of documents |
| Knowledge base with human validation (Should) | Consolidation of the company-wide talent database |
| Handoff to IGS with accelerated timing (Could) | Production rollout across all locations |

### Demo scenario

1. The start email arrives for a W-2 consultant in Philadelphia, with the timesheet approver blank and a contradictory work arrangement.
2. The Coworker alerts the recruiter with the two exact fields; the recruiter answers in the chat.
3. The Coworker recommends the paperwork (non-exempt agreement and Philadelphia forms), the owner and, if S1 is ready, email, apps and an INSPYR laptop with 2% overhead.
4. The Coworker notifies the Consultant Onboarding Supervisor of the new person so she can assign the follow-up owner.
5. The Coworker notifies the follow-up owner on the Onboarding Team and hands over the package with sources so they can approve the consolidated information.
6. The Onboarding Team can ask the Coworker at any time about the status of their candidates; the Coworker checks JobDiva and answers in the chat.
7. When it applies, the Coworker sends the request to IT to approve the laptop.
8. The Coworker creates the case in the JobDiva mock, the access and equipment requests and the task list; everything is logged and updated as each process completes.
9. A second attempt with the same person and date is blocked as a duplicate.

## 4. Current and redesigned process

The redesign moves validation to the start: today gaps are found once onboarding already has the case; with the Coworker, nothing reaches onboarding incomplete.

### Current process (INSPYR)

Today, gaps are found once onboarding already has the case. Steps marked ⚠ are pain points.

| Step | Lane | Activity |
| --- | --- | --- |
| 1 | Recruiter | Submits the start |
| 2 | JobDiva | Sends the automatic email |
| 3 | Onboarding | ⚠ Builds the case and chases gaps, with back-and-forth to the recruiter |
| 4 | Onboarding | ⚠ Picks the paperwork |
| 5 | Candidate | Signs the documents |
| 6 | Onboarding | Reviews and approves |
| 7 | Payroll | ⚠ Builds a manual report |

In parallel, ⚠ the recruiter requests the laptop from Chelsea Tech outside the flow.

### Pain points

| Pain point | Effect | How the Coworker solves it |
| --- | --- | --- |
| Start notes are optional and arrive blank | Back-and-forth with the field before work can start | The 7 fields are validated on arrival and the recruiter gets the exact field |
| Work arrangement asked in three JobDiva places | Contradictory values | One confirmed answer feeds every record |
| Paperwork depends on tacit knowledge (FLSA, state, city, client) | Wrong or missing forms | A rule engine recommends and cites the rule |
| Cases created by hand and assigned by flagging emails by division | Repetitive work | Prefilled case and suggested owner |
| Repeatedly checking JobDiva to see status | Lost time | Automatic reminders and alerts only when needed |
| Equipment requested from Chelsea Tech outside the flow | Overhead and bill-back missed | Equipment, provider and overhead in the same request, approved by IT |
| Manual payroll report reconciled with a Google Doc | Missed starts and returns | Payroll package and returns as tasks |
| Process knowledge held by a few people | Dependency and loss if someone leaves | Validated, searchable knowledge base |

### Redesigned process

With the Coworker, nothing reaches the approver incomplete.

| Step | Lane | Activity |
| --- | --- | --- |
| 1 | Recruiter | Sends the start by email or chat |
| 2 | Coworker | Extracts and validates the data; the recruiter fixes any flagged field |
| 3 | Coworker | Determines path, paperwork and access |
| 4 | Coworker | Builds the package with sources |
| 5 | Approvers | **Human decision:** Tonya Ramirez approves the package; IT approves the laptop |
| 6 | Simulated systems | **After approval:** creates the case and tasks |
| 7 | Candidate | Receives the checklist and alerts (Should) |

Throughout, the Coworker updates JobDiva at each stage.

The recruiter fixes only the flagged field, before onboarding steps in. To every user it is one Coworker that keeps JobDiva updated at each stage; inside, each step is handled by a specialized agent. Nothing reaches any system without the Consultant Onboarding Supervisor’s approval, and IT’s when there is a laptop.

### What the user sees

Two screens summarize the experience: the intake conversation and the package the approver reviews. The data is synthetic.

**Screen 1: intake conversation (case ONB-0142).** The Coworker asks only for the two missing fields.

> **Coworker:** Start received for Jordan Perez: W-2, Philadelphia (PA), client Acme Health. 2 fields are missing before onboarding:
> - Timesheet approver: blank
> - Work arrangement: Remote in the note, Onsite in the job
>
> **Recruiter:** Approver: Dana Lee. It is hybrid, 3 days on site.
>
> **Coworker:** Thanks. I recommend:
> - Non-exempt agreement and Philadelphia forms · rule R-PA-02
> - Email, Teams and INSPYR laptop, 2% overhead · rule R-EQ-01
>
> [Send for approval] [Fix data] · Status: ready for review

**Screen 2: approval package, ONB-0142, version 2.** Jordan Perez · Data Analyst · Acme Health · starts Nov 1 · approver: Tonya Ramirez · status: ready for review.

| Data | Value | Label | Source |
| --- | --- | --- | --- |
| Path | W-2 · non-exempt | Source | Recruiter note |
| Location | Philadelphia, PA · hybrid | Source | Recruiter, in chat |
| Timesheet | Dana Lee | Source | Recruiter, in chat |
| Paperwork | Non-exempt + PA forms | Recommended | Rule R-PA-02 |
| Owner | Onboarding, Healthcare division | Recommended | Rule R-OWN-03 |
| Access | Email, Teams, Office | Recommended | Access catalog |
| Equipment | INSPYR laptop · 2% overhead | Recommended | R-EQ-01 · IT approves |
| Bill-back | Does the client pay for the laptop? | Exception | No client rule |

Footer: 14 audit log events · 1 open exception · no duplicates. Actions: Approve, Return for correction, Reject, View in JobDiva.

The approver can tell at a glance what came from a source, what the Coworker recommends and what is still open. An open exception, such as bill-back with no client rule, is visible before approval.

## 5. Solution design

To users, the Coworker is a single agent with several touchpoints (email, chat and notifications) that proposes drafts and keeps JobDiva updated at each stage. Inside, an Onboarding Orchestrator owns the case and splits the work across specialized agents that share the same context; only one of them writes to the simulated systems, and only with approval. This multi-agent architecture is what the hackathon scores.
| Agent | Priority | Responsibility | Tools |
| --- | --- | --- | --- |
| Onboarding Orchestrator | Must | Keeps the case status, decides which agent acts, manages timing and escalations, builds the package, enforces the approval gate and answers the Onboarding Team about their candidates | Case store, audit log, notifications, JobDiva lookup |
| Intake and Validation | Must | Reads the email or chat, extracts the fields, checks completeness and consistency, asks for what is missing and checks for duplicates | Mailbox (mock), JobDiva search (mock) |
| Policy and Case Setup | Must | Applies the rule engine: path, agreement by FLSA, forms by state, city and client; recommends the owner; escalates unclear cases to the Onboarding Team | Rules catalog |
| JobDiva and Workflow | Must | After approval, creates the JobDiva case and updates it at each stage; creates requests, the task list and the payroll package | JobDiva, IT, equipment and payroll mocks |
| Access and Equipment | Should | Recommends email, Teams, apps and equipment; computes overhead and bill-back; drafts the Chelsea Tech request | Access and equipment catalogs |
| Candidate Follow-up | Should | Sends the checklist, tiered reminders and correction requests; verifies what was delivered | Notifications (mock), checklist |
| Onboarding Knowledge | Should | Answers process questions from validated records and cites the source; proposes drafts and logs unresolved questions | Knowledge base |
| Culture and Belonging (IGS) | Could | Logs the hire in the LDC tracker, assigns the kit, schedules feedback and drafts the congratulation | LDC list (mock), notifications |

Notifications (email and Teams) are a shared tool with templates per audience, not a separate agent. The demo shows at least three specialized agents collaborating on one case: Intake, Policy and JobDiva, coordinated by the orchestrator; Access and Equipment joins if S1 is ready.

### Case states

Each case moves through explicit states and a single approval gate. 👤 = a person steps in; ⛔ = the case stops; (Should/Could) = extension.

| State | Next |
| --- | --- |
| Received | Validated; or ⛔ Blocked: duplicate |
| Validated | Case set up; if data is missing, 👤 Needs clarification (returns to Validated when answered) |
| Case set up | Ready for review |
| Ready for review | 👤 Approval gate |
| 👤 Approval gate | Approved; ⛔ Rejected; or returned for correction (back to Validated) |
| Approved | Actions executed |
| Actions executed | Documents pending (Should) |
| Documents pending (Should) | 👤 In verification (Should) |
| 👤 In verification (Should) | 👤 Sent to payroll (Should) |
| 👤 Sent to payroll (Should) | Handoff to IGS (Could) |
| Handoff to IGS (Could) | Closed |

### Demo sequence

Four agents and three people resolve the case in thirteen messages. Every message is logged with its agent, its data and its rules.

| # | From | To | Message |
| --- | --- | --- | --- |
| 1 | Recruiter | Orchestrator | Sends the start |
| 2 | Orchestrator | Intake | Validate |
| 3 | Intake | Orchestrator | 2 fields missing |
| 4 | Orchestrator | Recruiter | Asks for the 2 fields |
| 5 | Recruiter | Orchestrator | Answers |
| 6 | Orchestrator | Policy | Paperwork |
| 7 | Orchestrator | Access | Equipment |
| 8 | Policy | Orchestrator | Rule R-PA-02 |
| 9 | Access | Orchestrator | Laptop, 2% overhead |
| 10 | Orchestrator | Tonya Ramirez and IT | **Package v2 for approval** |
| 11 | Tonya Ramirez and IT | Orchestrator | **Approved** |
| 12 | Orchestrator | Mocks | Create the case |
| 13 | Mocks | Orchestrator | IDs created |

## 6. Data, tools, integrations and simulated services

Every enterprise system is a simulated service (mock) exposed as a tool or MCP server; business rules and knowledge live as data the business maintains, not in code.

### Integrations

| System | Use in the Coworker | In the hackathon | Agent using it |
| --- | --- | --- | --- |
| Velocity 2.0 | Agent runtime, orchestration and models | Real (mandatory) | All |
| JobDiva | Search starts (duplicates), create the case, read activated documents and status | API mock by default; sandbox read-only if API credentials are obtained | Intake, JobDiva and Workflow |
| Onboarding mailbox (Outlook) | Read the start email, send notifications | Mock with synthetic emails | Intake, notifications |
| Microsoft Teams | Alerts to owners, IT and LDC; optional chat channel | Mock | Notifications |
| IT and equipment (Chelsea Tech) | Access and laptop requests approved by IT | Mock; never real orders | Access and Equipment, JobDiva and Workflow |
| Payroll (Paychex) | Receive the package and return issues | Mock | JobDiva and Workflow |
| LDC tracker (SharePoint) | Hire log, kit and feedback | List mock; owner: the LDC team | Culture and Belonging |
| Knowledge base | Validated questions, solutions and procedures | Seed data | Knowledge |

### Functional prototype and channels

The demo runs in a lightweight local web app connected to the orchestrator on Velocity 2.0; it is the only mandatory channel and depends on no outside permissions.

| View | Who uses it | What it shows |
| --- | --- | --- |
| Chat | Recruiter and Onboarding Team | The conversational intake and status questions (“how are my candidates doing?”) |
| Simulated email inbox | Demo | Synthetic start emails; a button simulates a new one arriving |
| Approval | Tonya Ramirez | The package with sources and the Approve, Return and Reject buttons |
| Simulated alerts | Everyone | The notifications that would go through Teams or email in production |
| Status | Onboarding Team and reviewers | The case in the JobDiva mock, the requests and the audit log |

**Team decisions:** Velocity 2.0 has no chat interface of its own, so we build the web app. Nobody on the team has permission today to register a bot in the INSPYR tenant; the Teams integration is optional if permissions are obtained, and only after the demo is stable. In the pilot, the same orchestrator connects to Teams and the real onboarding mailbox without changing the agents.

### JobDiva integration and authentication

The demo uses the JobDiva mock; the real sandbox is an optional read-only mode, switched on by an environment variable if we get API credentials in time.

- **One connector, two modes.** The agents always call the same JobDiva connector (MCP server). `JOBDIVA_MODE=mock` (default) creates and updates the case with synthetic data; `JOBDIVA_MODE=sandbox` only reads: a test candidate’s start, its start notes and the duplicate search. The Coworker never writes to JobDiva, not even in the sandbox.
- **API authentication, not the web login.** A user login to the sandbox web interface does not work for the Coworker. The API needs the account’s Client ID (issued by JobDiva support), a dedicated API user (created by an admin with the “Only allow access to JobDiva API Calls” permission) and its password; these return a token that is renewed when it expires. Based on integrator guides; to be confirmed with JobDiva.
- **Secrets.** `JOBDIVA_BASE_URL`, `JOBDIVA_CLIENT_ID`, `JOBDIVA_API_USER` and `JOBDIVA_API_PASSWORD` go in a local `.env` outside the repository; the repository only ships `.env.example` with the names. The token lives in memory and is never written to the audit log.
- **Manual use of the sandbox.** The team’s web access is used to copy the real start form fields, export test start emails for the simulated inbox and review the document packages that feed the rules catalog.

**Pending:** ask Tonya Ramirez or the account admin to have JobDiva enable the API on the sandbox and create the API user, and confirm read-only sandbox use with the committee. If there are no credentials by October 16, the demo continues with the mock only.

### Data model

| Entity | Main fields |
| --- | --- |
| Onboarding case | ID, person, role, client, division, location, contract type, FLSA, sponsorship, owner, status, dates, package version |
| Package line | Case, field, value, label (source, inferred, recommended, exception), source or rule ID |
| Approval | Case, version, approver, decision, comment, date |
| Document checklist | Case, document, required by (client, location, contract), status, date |
| Business rule | ID, type (contract to kit, client to documents, location to documents, contract or client to owner, equipment to overhead), condition, result, owner |
| Cultural follow-up | Person, leader, start, kit, feedback date, status, congratulation |
| Knowledge record | ID, type, title, description, answer, steps, category, tags, status, source, date |
| Audit log | Action, agent, case, date, data and rules used |

**Seed data:** path and form rules (for example California, Philadelphia, and Texas with no state forms), 2% and 5% overhead, access catalog, and synthetic W-2, contractor and corp-to-corp scenarios with gaps, contradictions and a duplicate.

### Onboarding knowledge module

It preserves operational knowledge so that, if the onboarding owner leaves, someone else can ask the Coworker for the questions, solutions and procedures already documented. The repository grows with every resolved case, without documenting the whole process up front.

| Operation | Purpose |
| --- | --- |
| searchKnowledge / getKnowledge | Find and retrieve validated records, citing the source |
| createKnowledge / updateKnowledge | Log or enrich a question, problem or procedure |
| submitForValidation / validateKnowledge | Send for validation and record the owner’s decision |
| registerUnresolved | Keep an unanswered question pending |
| getKnowledgeHistory | See a record’s versions, dates and change origin |

**Agreed decision.** The agent proposes drafts when it has the context, marked as unvalidated; the right person for the case approves them before they are presented as confirmed (RN-03 and RN-04).

## 7. Governance, acceptance criteria, risks and plan

People keep every decision that creates a record, grants access, spends money or touches employment law; the Coworker prepares, recommends, cites and logs.

### Governance model

| Control | How it is enforced |
| --- | --- |
| Approval gate | Tools that write to systems run only with an approval ID for the current package version |
| No legal decisions | FLSA, classification and compensation come from the field or HR; the Coworker only maps them to paperwork and escalates conflicts to the Onboarding Team |
| Rules owned by the business | Onboarding, IT and LDC maintain the rules as data, with an owner and a version |
| Traceability | Each data point carries its label (source, inferred, recommended, exception) and each action is in the audit log |
| Sensitive data | Visa, sponsorship and FLSA restricted by role; never in messages to leaders or mass communications |
| Duplicate prevention | A request or case with the same person and date is searched for before continuing |
| Data and secrets | Synthetic data only, no production connections, no credentials in the repository |
| Message cadence | Reminders with configurable frequency and a send limit |
| Cost | Model use within the assigned budget and logged per run |

**Seven human checkpoints:** the recruiter corrects the flagged data; the Onboarding Team confirms the case and owner and resolves process escalations; the Consultant Onboarding Supervisor (Tonya Ramirez) approves the package; IT approves the laptop; onboarding approves the payroll handoff; LDC approves the welcome kit and feedback; the right person for the case validates new knowledge.

### Acceptance criteria

| # | Criterion | Priority |
| --- | --- | --- |
| AC1 | Given an email with a missing or inconsistent field, the recruiter gets an alert naming the exact field | Must |
| AC2 | The intake collects 100% of the scenario’s mandatory data without questions outside the path | Must |
| AC3 | Given a client, location and contract, the paperwork and owner match the configured rules | Must |
| AC4 | Equipment and its overhead match the provider (2% or 5%) and the laptop is not requested without IT approval | Should |
| AC5 | The package is ready in 5 minutes or less after the last answer and every line cites its source | Must |
| AC6 | No action on simulated systems happens without approval of the current package version | Must |
| AC7 | A duplicate request is blocked | Must |
| AC8 | At least three specialized agents (Intake, Policy and JobDiva) collaborate on the same case, coordinated by the orchestrator | Must |
| AC9 | Every agent action is in the audit log | Must |
| AC10 | If the candidate misses a deadline they get a reminder and, past the threshold, the owner gets an alert | Should |
| AC11 | The knowledge agent answers with the record reference or leaves the question pending; it never presents unvalidated content as confirmed | Should |
| AC12 | Closing the onboarding creates the LDC tracker entry with the kit by contract, and the congratulation needs LDC approval | Could |

### Key risks

Preliminary team assessment (October 14); the timeline is the only risk high in both impact and likelihood.

| # | Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | 8 days to build and test | High | High | Build J1 and J2 end to end first; Should and Could only with a stable demo |
| R2 | Velocity 2.0 learning curve or licenses | High | Medium | Confirm licenses on October 15; a minimal case working on day one |
| R3 | Tacit business rules (forms, overhead, bill-back) | High | Medium | Validate the rules catalog with Tonya Ramirez’s team; cite rule IDs |
| R4 | Recruiting emails with no standard format | Medium | High | The agent tolerates variations and asks for confirmation; propose a template |
| R5 | Extraction errors affecting payroll or classification | High | Low | Mandatory human validation; no autonomous decisions |
| R6 | Exposure of visa, sponsorship or FLSA | High | Low | Role-based permissions and data minimization in messages |
| R7 | Too many reminders to candidates or leaders | Low | Medium | Configurable cadence and a send limit |
| R8 | Model cost overrun | Medium | Low | Small models for extraction, usage logged per run |
| R9 | Low adoption by the teams | Medium | Medium | Co-design with onboarding and LDC; the Coworker assists, it does not replace |
| R10 | Demo failure on presentation day | High | Low | Preloaded scenarios and a backup video |
| R11 | JobDiva API credentials not available in time | Low | High | JobDiva mock as the default mode; the sandbox is enabled only if credentials arrive before October 16 |

### Implementation plan

Eight days: two for foundations, four for journeys, two to wrap up. Extensions run in parallel only if the Must items are stable.

| Dates | Work |
| --- | --- |
| October 14 | Checkpoint |
| October 15–16 | Foundations and mocks |
| October 17–20 | Journeys J1 and J2 (Must) |
| October 19–20 | Extensions (Should), in parallel |
| October 21–22 | Tests, README and video |
| October 22 | **Final submission** |

October 16 is the key cutoff: if Velocity 2.0, the database and the mocks are not ready, the extensions are dropped and all time goes to J1 and J2.

| Phase | Scope | Result |
| --- | --- | --- |
| Hackathon (until October 22) | Journeys J1 and J2 with mocks; J3, knowledge and IGS if time allows | End-to-end demo, repository, README, presentation and video |
| Pilot (4 to 6 weeks) | One client or contract type, real onboarding mailbox, real JobDiva integration | Measurement against the 3-day baseline |
| Scale-up | All clients, full document verification, full IGS flow and analytics | Stable operation and continuous improvement |
