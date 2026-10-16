# Source of Truth: Onboarding Digital Coworker

**Project:** Onboarding Digital Coworker
**Document ID:** SOT-001
**Stage:** 01 — Functional Understanding
**Date:** 2026-10-16
**Version:** 1.0

---

## Glossary

> This document uses ID-prefixed catalogs (CAP-XXX, BR-XXX, and the like) as shorthand once you're used to them, but they mean nothing on first read. This table is the decoder ring, covering only the terms this document actually uses.

| Term | Meaning |
|------|---------|
| SOT | Source of Truth — this document's own ID prefix (e.g. SOT-001) |
| STK-XXX | Stakeholder — an entry in §2 |
| UR-XXX | User Role — an entry in §3 |
| CAP-XXX | Capability/Feature — an entry in §4; what `functional-spec` traces its FR-XXX catalog back to |
| BR-XXX | Business Rule — an entry in §5 |
| CONST-XXX | Constraint (business/legal) — an entry in §6 |
| INT-XXX | External Integration (the business need for it, not its technical mechanics) — an entry in §7 |
| ASM-XXX | Assumption — an entry in §8 |
| INC-XXX | Resolved Inconsistency — an entry in §9's log |
| OQ-XXX | Open Question — an entry in §10, a gap resolved with a flagged logical default pending confirmation |
| PO/BSA | Product Owner / Business Systems Analyst — the role responsible for approving this phase (§13) |

*(Downstream documents — Strategic Intake, Functional Spec, Backlog — introduce their own IDs, like FR-XXX and US-XXX, and define them in their own Glossary section instead of here.)*

---

## 1. Idea, Definition & Scope

> This section is what `strategic-intake` draws from most directly to land the client's idea into a concrete project concept.

### 1.1 Idea
A digital coworker for the INSPYR onboarding team. It takes in a new hire's start by email or chat, checks that the data is complete and consistent, recommends the paperwork path and onboarding owner, and prepares an approval package. Every action is taken only after a person approves it.

### 1.2 Definition
The Onboarding Digital Coworker is an assistant that supports the onboarding process from the moment a recruiter submits a start until the validated package is handed to Payroll (and, optionally, to IGS). It does not take legal, classification or compensation decisions. It does not write to the real JobDiva. In this hackathon release it runs against synthetic data and simulated systems.

### 1.3 Description
**Current situation.** At INSPYR, gaps in a new hire's data are found only after the onboarding team already has the case.
- JobDiva start notes are optional and often blank.
- Work arrangement is asked in three places and gives contradictory values.
- Paperwork depends on tacit knowledge (FLSA, state, city, client).
- Cases are created by hand.
- Equipment is requested outside the flow.
- The payroll report is built manually.
- Process knowledge is held by a few people.

**Business problem.** Onboarding teams spend time chasing missing or inconsistent data from recruiters, picking paperwork from tacit rules and rebuilding information by hand. The result is:
- slow document onboarding (about 3 days);
- wrong or missing forms;
- missed overhead and bill-back;
- payroll returns;
- dependence on a few people's knowledge.

**Why now.** The hackathon has a fixed final submission on October 22, 2026, about eight days of build time after the October 14 checkpoint. October 16 is the cutoff for the foundations. If they are not ready, the extensions are dropped and all effort goes to the two Must journeys.

**Current alternative.**
1. The recruiter submits the start in JobDiva and an automatic email goes out.
2. The onboarding team builds the case by hand, chases gaps with the recruiter and picks the paperwork from tacit knowledge.
3. The candidate signs and onboarding reviews.
4. Payroll builds a manual report.
5. The recruiter separately requests the laptop from Chelsea Tech.

### 1.4 Scope
**In Scope:**
- Intake by email and chat with adaptive questions.
- Validation of the 7 recruiter-note fields and the consistency rules.
- Business rules for paperwork (contract type, FLSA, state, city, client), onboarding owner (client type and role) and welcome kit (contract type).
- Access, equipment, overhead and bill-back (Should).
- Approval package and human approval gate.
- Simulated JobDiva, IT, equipment, payroll and email actions.
- Follow-up with a synthetic candidate (Should).
- Knowledge base with human validation (Should).
- Handoff to IGS with accelerated timing (Could).

**Out of Scope:**
- Recruiting inside JobDiva before the notification.
- Legal classification or compensation decisions.
- Background checks, drug screens, I-9 and E-Verify.
- Real equipment purchases or provisioning.
- Payroll processes after the handoff.
- Production JobDiva integration and real data.
- Real e-signature and legal validation of documents.
- Consolidation of the company-wide talent database.
- Production rollout across all locations.
- The Coworker never writes to the real JobDiva.

**Won't v1 (deferred past v1):**
- The pilot (4 to 6 weeks: one client or contract type, real onboarding mailbox, real JobDiva integration).
- The scale-up (all clients, full document verification, full IGS flow, analytics).
- Microsoft Teams as a channel is optional and only added after the demo is stable.
- Should and Could items are built only if the Must journeys are stable.

### 1.5 Expected Value
- Document onboarding time from about 3 days to 1 to 1.5 days (pilot).
- Zero cases reaching onboarding with missing data and no alert.
- 100% of mandatory data complete in the test scenario.
- A package ready for approval within 5 minutes of the last answer.
- Zero actions executed without approval.
- A measurable reduction in payroll returns (pilot).
- A business reviewer score of 4 out of 5 or higher.

---

## 2. Stakeholders

| ID | Name | Role | Influence / Decision |
|----|------|------|-----------------------|
| STK-001 | Tonya Ramirez | Consultant Onboarding Supervisor (business owner) | Is notified of each new hire, assigns the follow-up owner, approves, returns or rejects the package |
| STK-002 | Onboarding Team | Onboarding operations | Reviews and confirms the case, path and owner; handles escalations; approves the payroll handoff; countersigns document verification; validates knowledge |
| STK-003 | Recruiter or hiring manager | Case originator | Starts the case and corrects flagged data |
| STK-004 | IT | Systems and equipment | Approves the laptop together with the package |
| STK-005 | HR | Human Resources | Owns legal and classification answers |
| STK-006 | Candidate (new hire) | Onboarding participant | Receives the checklist and reminders |
| STK-007 | Payroll | Payroll operations | Receives the validated package |
| STK-008 | LDC (IGS) | Downstream onboarding team | Owns its tracker; approves the welcome kit, feedback and congratulation |
| STK-009 | Juan Carlos Giron | Product Owner / BSA (project team) | Product Owner / BSA for this project; responsible for approving this phase (see §13) |
| STK-010 | Viviana Gomez | Project team member (specific role not stated) | Project team |
| STK-011 | Laura Hernandez | Project team member (specific role not stated) | Project team |
| STK-012 | David Valdez | Project team member (specific role not stated) | Project team |
| STK-013 | Carlos Puerta | Project team member (specific role not stated) | Project team |
| STK-014 | Michael Erskin | Project team member (specific role not stated) | Project team |

---

## 3. User Roles

| ID | Role Name | Description |
|----|-----------|-------------|
| UR-001 | Recruiter or hiring manager (primary) | Starts the onboarding case, answers the Coworker's adaptive questions and corrects flagged data |
| UR-002 | Onboarding Team (primary) | Reviews and confirms the case, path and owner, handles escalations and asks the Coworker for case status in chat |
| UR-003 | Approver — Consultant Onboarding Supervisor (secondary) | Approves, returns or rejects the approval package |
| UR-004 | IT (secondary) | Approves the laptop request together with the package |
| UR-005 | HR (secondary) | Owns legal and classification answers |
| UR-006 | Candidate (secondary) | Receives the checklist and reminders |
| UR-007 | Payroll (secondary) | Receives the validated package and returns issues |
| UR-008 | LDC / IGS (secondary) | Receives the handoff and owns its own tracker |

---

## 4. Capabilities / Features

> The stable catalog both `functional-spec` (as FR-XXX) and `backlog` (as user stories) trace back to. Capabilities are described in terms of what they do for the user or business, never how they're built.

| ID | Capability | Description | Key Behaviors | Priority (if stated) |
|----|-----------|--------------|----------------|-----------------------|
| CAP-001 | Case intake | Starts a case from the JobDiva start email or from chat | Accepts the start email or a chat request | Must |
| CAP-002 | Adaptive questions | Asks for whatever information is missing | Questions adapt to the gaps found | Must |
| CAP-003 | Completeness and consistency check | Checks the 7 recruiter-note fields and the mandatory data | Alerts the recruiter with the exact field that is missing or inconsistent | Must |
| CAP-004 | Path and paperwork recommendation | Recommends the onboarding path and the paperwork | Cites the rule ID behind each recommendation | Must |
| CAP-005 | Onboarding owner recommendation | Recommends who owns the onboarding follow-up | Based on client type and role | Must |
| CAP-006 | Approval package | Assembles the package a person reviews | Every data point carries a label and a source | Must |
| CAP-007 | Approval gate | Lets the approver decide on the package | Approve, return or reject | Must |
| CAP-008 | Simulated actions after approval | Runs actions on simulated systems | Only after approval | Must |
| CAP-009 | Duplicate prevention and audit log | Prevents duplicate cases and records what the agent does | Duplicates blocked; every action logged | Must |
| CAP-010 | Status questions in chat | Answers the Onboarding Team's questions about a case | Status asked and answered in chat | Must |
| CAP-011 | Access and equipment | Handles access and equipment requests | Includes overhead and bill-back | Should |
| CAP-012 | Candidate checklist and tiered reminders | Sends the candidate a checklist and follows up | Tiered reminders | Should |
| CAP-013 | Delivered-document check | Checks the documents the candidate delivers | Verification of delivered documents | Should |
| CAP-014 | Payroll package and returns | Prepares the package for Payroll and tracks returns | Package handoff and issues returned | Should |
| CAP-015 | Knowledge base with human validation | Keeps onboarding knowledge that people validate | Unvalidated knowledge is not presented as confirmed | Should |
| CAP-016 | IGS handoff | Hands the case to IGS | Accelerated timing | Could |
| CAP-017 | Leader feedback and congratulation | Collects leader feedback and sends a congratulation | Feedback and congratulation approved by LDC (IGS) | Could |
| CAP-018 | Status dashboard | Shows case status | Not further specified | Could |
| CAP-019 | New-hire information package | Provides information to the new hire | Not further specified | Could |

---

## 5. Business Rules

| ID | Rule | Source |
|----|------|--------|
| BR-001 | FLSA, classification and compensation come from the field or HR. Conflicts escalate to the Onboarding Team, and HR owns the legal answer | Answers record, `business-rules.list` |
| BR-002 | Actions on systems happen only with approval of the current package version | Answers record, `business-rules.list` |
| BR-003 | A returned package needs a new approval; a rejected case stops | Answers record, `business-rules.list` |
| BR-004 | Duplicates (same person and start date) are blocked | Answers record, `business-rules.list` |
| BR-005 | Work arrangement has one confirmed answer | Answers record, `business-rules.list` |
| BR-006 | Rules are maintained by Onboarding, IT and LDC with an owner and version, and are cited by ID | Answers record, `business-rules.list` |
| BR-007 | Equipment overhead is 2% (INSPYR) or 5% (Apple Direct) | Answers record, `business-rules.list` |
| BR-008 | Bill-back is per client; with no client rule it appears as an exception | Answers record, `business-rules.list` |
| BR-009 | The onboarding owner is recommended by client type and role | Answers record, `business-rules.list` |
| BR-010 | Reminders go out at 24 h and 48 h, then escalate, with configurable cadence and send limit | Answers record, `business-rules.list` |
| BR-011 | Visa, sponsorship and FLSA are restricted by role and never appear in messages to leaders or mass communications | Answers record, `business-rules.list` |
| BR-012 | IT approves the laptop together with the package | Answers record, `business-rules.list` |
| BR-013 | Unvalidated knowledge is never presented as confirmed | Answers record, `business-rules.list` |
| BR-014 | The Coworker never writes to the real JobDiva | Answers record, `business-rules.list` |

---

## 6. Constraints

> Business/legal constraints only — budget, policy, regulation, vendor agreements. Technical constraints belong in Technical Validations instead.

| ID | Type | Constraint | Source |
|----|------|-----------|--------|
| CONST-001 | Schedule | Final submission on October 22, 2026, with October 16 as the cutoff for the foundations | Answers record, `constraints.list` |
| CONST-002 | Budget | Model usage must stay within the assigned budget | Answers record, `constraints.list` |
| CONST-003 | Data | Synthetic data only | Answers record, `constraints.list` |
| CONST-004 | Legal / Policy | No legal decisions by the Coworker | Answers record, `constraints.list` |
| CONST-005 | Organizational access | Nobody on the team can register a bot in the INSPYR tenant, so Microsoft Teams is optional | Answers record, `constraints.list` |

---

## 7. External Integrations

> The business need for an integration, not its technical mechanics. For the hackathon, all of these are simulated.

| ID | System | Purpose | Source |
|----|--------|---------|--------|
| INT-001 | JobDiva | Start data, duplicate search, case and status; never writes to the real one | Answers record, `integrations.list` |
| INT-002 | Onboarding mailbox (Outlook) | Start emails and notifications | Answers record, `integrations.list` |
| INT-003 | Microsoft Teams | Alerts; optional | Answers record, `integrations.list` |
| INT-004 | Chelsea Tech | Access and laptop requests approved by IT; never real orders | Answers record, `integrations.list` |
| INT-005 | Paychex | Receives the payroll package and returns issues | Answers record, `integrations.list` |
| INT-006 | LDC tracker (owned by the LDC team) | IGS handoff | Answers record, `integrations.list` |
| INT-007 | Onboarding knowledge base | Holds validated onboarding knowledge | Answers record, `integrations.list` |

---

## 8. Assumptions

| ID | Assumption | Would Change the Project If Wrong? |
|----|-----------|--------------------------------------|
| ASM-001 | Velocity 2.0 licenses and JobDiva API credentials are pending confirmation as of October 16 | Yes — the build and integration plan depends on them |
| ASM-002 | Recruiter emails have no standard format, so variations are tolerated and confirmation is asked | No — the project already accounts for varied formats by asking for confirmation |
| ASM-003 | The rules catalog (forms by state and city, overhead, bill-back) is still being validated with Tonya Ramirez's team | Yes — path, paperwork and cost recommendations rely on these rules |
| ASM-004 | Should and Could items are built only if the Must journeys are stable | Yes — it determines how much scope is delivered by the deadline |

---

## 9. Resolved Inconsistencies Log

| ID | Subject | Options Presented | Resolution Chosen | Resolved By | Date |
|----|---------|--------------------|--------------------|-------------|------|
| — | None | — | — | — | — |

No inconsistencies (INC-XXX) were found or resolved in this round, so the log is empty.

---

## 10. Open Questions

| ID | Subject | Logical Default Applied | Why It's Open |
|----|---------|--------------------------|-----------------|
| OQ-001 | Sprint velocity | Recorded in §13 as "Not applicable": the team plans by dates (October 15 to 22) rather than by sprints, so no sprint velocity is estimated. If a figure is needed for the backlog, it would be sized to the Must journeys J1 and J2 within the date plan | The material says the team plans by dates, not sprints, and gives no velocity figure |
| OQ-002 | Definition of Done | Recorded in §13: a story is done when it meets its acceptance criteria, has been demonstrated end to end on synthetic data in the local demo, and writes every agent action to the audit log. Any action on a simulated system runs only with an approval ID for the current package version. It is reviewed by a team member and accepted by the Product Owner | No Definition of Done is stated; built from the project's own acceptance criteria and governance rules plus a standard peer-review and Product Owner acceptance step |

---

## 11. Source Inventory

| # | Source | Type | Used For |
|---|--------|------|----------|
| 1 | Answers record from the Phase 1 context analysis (`1-functional-understanding-context-analysis`) | Structured, keyed record | Every fact in this document. The individual files behind it are not itemized in the record |

---

## 13. Team Process Parameters

> Not business/discovery facts about the project itself. These are team-capacity and quality-bar answers, resolved during context analysis so `backlog` never has to ask for them later.

**PO/BSA Name:** Juan Carlos Giron (also recorded as a stakeholder in §2, STK-009, with role "Product Owner / BSA")
**Sprint Velocity:** Not applicable. The team plans by dates (October 15 to 22) rather than by sprints, so no sprint velocity is estimated. If a figure is needed for the backlog, it would be sized to the Must journeys J1 and J2 within the date plan. *(Assumed default — see OQ-001)*
**Definition of Done:** A story is done when it meets its acceptance criteria, has been demonstrated end to end on synthetic data in the local demo, and writes every agent action to the audit log. Any action on a simulated system runs only with an approval ID for the current package version. It is reviewed by a team member and accepted by the Product Owner. *(Assumed default — see OQ-002)*