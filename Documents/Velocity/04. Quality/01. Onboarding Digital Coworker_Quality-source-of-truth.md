# Quality Source of Truth: Onboarding Digital Coworker

**Project:** Onboarding Digital Coworker
**Document ID:** QSOT-001
**Stage:** 04 — Quality
**Related Functional Requirements Specification:** FRS-001
**Related NFR Register:** Not identified by document ID in the Answers record (NFR-XXX targets are cited individually below)
**Related Software Architecture Document:** Not identified by document ID in the Answers record
**Related Testing Information:** `documentation/SharedDocs/testing-information.json` (TIC-003 cited in the Answers record)
**Date:** 2026-10-26
**Version:** 1.2 (manual review edits on top of the generated 1.0, aligned with the repository at commit efe5b3e and SAD ADR-006; regenerating this document from the Answers record discards them)

> Never redecides a functional requirement or a non-functional target. The FR-XXX catalog and the NFR-XXX targets, each with the verification method Architecture chose for it, are fixed inputs from Phases 1 and 2. This document decides how the system gets verified on top of them. It reads no Phase 3 document directly: whatever Development has already settled about testing reaches this document through `documentation/SharedDocs/testing-information.json`, cited in §1.2.

---

## Glossary

> This document uses ID-prefixed catalogs (SCOPE-XXX, LEVEL-XXX, and the like) as shorthand. This table decodes only the terms the document actually uses.

| Term | Meaning |
|------|---------|
| QSOT | Quality Source of Truth — this document's own ID prefix (e.g. QSOT-001) |
| SCOPE-XXX | Test Scope — what QA will and won't test, with a rationale for every exclusion; an entry in §2 |
| LEVEL-XXX | Testing Level & Ownership — a testing level this project needs, its owner, and whether it is automated or manual; an entry in §3 |
| ENV-XXX | Test Environment — an environment available for testing, or a dependency without a test mode and how it is handled; an entry in §4 and §4.1 |
| DATA-XXX | Test Data Management fact — data source, privacy obligation, volume requirement, or ownership; an entry in §5 |
| QTOOL-XXX | QA Tooling — a test management, QA automation, performance, defect tracking or CI tool; an entry in §6 |
| CRIT-XXX | Entry/Exit Criterion or Quality Metric — a condition for starting or completing a test cycle, or a reported metric and its target; an entry in §7 |
| DEF-XXX | Defect Management fact — severity definition, fix target, lifecycle state, or triage responsibility; an entry in §8 |
| TEAM-XXX | QA Team, Role or Schedule fact — who tests, allocation, cycle plan and fixed dates; an entry in §9 |
| TCCONV-XXX | Test Case Convention — ID format, priority scale, module grouping, or required fields; an entry in §10, the catalog `3-test-cases` reads to know what shape its output must take |
| INC-XXX | Resolved Inconsistency — an entry in §11's log |
| OQ-XXX | Open Question — an entry in §12, an assumption or item pending confirmation |
| FR-XXX | Functional Requirement — defined in the Functional Requirements Specification (FRS-001); what §2's scope covers and what the test cases must trace to |
| NFR-XXX | Non-Functional Requirement — defined in the NFR Register; every one with a measurable target is a testable target |
| ADR-006 | Architecture decision of 2026-10-26: Velocity 2.0 is the delivery method, not an agent runtime. Agents reach a model only through `agents/common/model_client.py`, with `MODEL_PROVIDER=rules` (no model, no key) as the default engine. It corrects TC-001 |
| TI / TIC-XXX | Testing Information, and its consistent items — the developer-level testing baseline recorded in `documentation/SharedDocs/testing-information.json`, cited in §1.2 |
| QUAL-XXX | Development quality target (Phase 3) — cited from Tech Doc §1 and Code Standards §6 |
| BR-XXX, TC-XXX, INF-XXX, SEC-XXX | Business rule, technology constraint, infrastructure fact and security fact from upstream phases, cited by ID where a test fact traces to one |
| J1 / J2 | The two demonstrated journeys: J1 (intake and validation) and J2 (package, approval, simulated actions) |
| MoSCoW | Priority scheme (Must / Should / Could) used by the Backlog, mapped to test priority in TCCONV-002 |

---

## 1. Quality Overview

### 1.1 System Context
Onboarding Digital Coworker is a multi-agent onboarding system built from scratch on synthetic data. An Onboarding Orchestrator coordinates specialist agents: Intake and Validation, Policy and Case Setup, and JobDiva and Workflow, plus Access and Equipment, Candidate Follow-up and Onboarding Knowledge if built. Every consequential action sits behind an approval gate tied to a specific package version, and every agent action is written to an audit log. All enterprise systems (JobDiva, Outlook mailbox, Teams, IT/equipment, payroll, LDC tracker, knowledge base) are mocked, and only simulated actions occur. The demonstrated journeys are J1 (intake and validation) and J2 (package, approval, simulated actions).

What has to be verified is:
- the Must functional requirements in FRS-001;
- every NFR with a measurable target;
- the inviolable governance rules, each through a negative test;
- a demo showing at least three agents collaborating on one case.

Submission and presentation are fixed for 2026-10-28, so testing runs as a single compressed cycle.

### 1.2 Testing Information Carried Forward (Not Decided Here)

The Answers record cites `testing-information.json` for one fact. The remaining developer-level baseline (QUAL-001 to QUAL-008) is cited from Tech Doc §1 and Code Standards §6 as assumed defaults. It is recorded in §3 and flagged in §12.

| TIC-XXX | What It Establishes | Consequence for This Phase |
|----------|----------------------|------------------------------|
| TIC-003 | Line coverage target of 70% (also QUAL-006). The Answers record flags it as an assumed default, not a confirmed target | Becomes a reported quality metric (CRIT-014) and a non-blocking exit target (CRIT-007), flagged as assumed — see OQ-001. `testing-information.json` is not in the repository; the same target is QUAL-006 (Tech Doc §1) |

---

## 2. Test Scope

> Scoped against the FRS-001 FR-XXX catalog and the NFR Register's NFR-XXX catalog. Every exclusion carries a rationale.

| ID | In / Out | Subject (FR-XXX, NFR-XXX, capability, component, or test type) | Rationale | Source |
|----|----------|-----------------------------------------------------------------|-----------|--------|
| SCOPE-001 | In | Journeys J1 (intake and validation) and J2 (package, approval, simulated actions); the Onboarding Orchestrator; the Intake and Validation, Policy and Case Setup, and JobDiva and Workflow agents; the approval gate; the audit log; the JobDiva connectors and mocks; and the negative governance tests | Must priority. The demo must show at least three agents collaborating on one case | `scope.list` |
| SCOPE-002 | In | Every in-scope Must FR in FRS-001, and every NFR with a measurable target | Must-priority requirements and measurable targets are the basis of coverage | `scope.list` |
| SCOPE-003 | In only if built | Access and Equipment, Candidate Follow-up and Onboarding Knowledge agents | Should priority. Controlled by FEATURE_* flags, off by default, so they are tested only if built. The same applies to the Should capabilities FR-ACC, FR-CHK, FR-DOC, FR-PAY and FR-KB. NFR-REL-004 (disable each Should agent in turn and run J1 and J2) is tested even when they are not built | `scope.list` |
| SCOPE-004 | Out | Culture and Belonging (IGS) agent and the Could stories (FR-IGS, FR-FBK, FR-DSH, FR-NHP) | Could priority and time is short | `scope.list` |
| SCOPE-005 | Out | Real systems, real orders and production access | The project is synthetic and simulated only (TC-002, TC-003, NFR-COMP-001) | `scope.list` |
| SCOPE-006 | Out | FLSA, classification, compensation and legal decisions | The system escalates these and never decides them (BR-001), so the test covers the escalation, not the decision | `scope.list` |
| SCOPE-007 | In (limited) | JobDiva sandbox mode | No sandbox credentials are confirmed. This is a declared risk, not coverage. Sandbox mode is tested only through negative and startup tests | `scope.list` |

---

## 3. Testing Levels & Ownership

> All developer-owned levels below are assumed defaults pending Development's confirmation (QUAL-001 to QUAL-008, Tech Doc §1, Code Standards §6) and are flagged in §12 (OQ-002). The last column records which NFR Verification Methods a level discharges.

| ID | Level | Applies? | Owner / Executed By | Automated / Manual / Both | Discharges NFR Verification Methods | Source |
|----|-------|----------|----------------------|----------------------------|--------------------------------------|--------|
| LEVEL-001 | Unit: rule lookups and case-state transitions. pytest, pytest-cov, unittest.mock (QUAL-002, QUAL-005). Mocks only at connector boundaries (MCP servers and the model client), never for case service or approval gate logic (QUAL-007) | Yes | Development team | Automated | — | `levels.list` |
| LEVEL-002 | Integration: connector tests in mock mode (QUAL-003) | Yes | Development team | Automated | — | `levels.list` |
| LEVEL-003 | System / end-to-end: J1 and J2 on the seed scenarios (QUAL-001). Agents run on the deterministic `rules` model engine (`MODEL_PROVIDER=rules`, SAD ADR-006), so the end-to-end runs need no model key and are repeatable. Free-form emails need a model engine and are outside this cycle (OQ-004) | Yes | Development team | Automated | — | `levels.list` |
| LEVEL-004 | Negative governance tests, one per inviolable rule (cases listed below the table). 100% must pass and any failure blocks merge (QUAL-004, QUAL-008) | Yes | Development team | Automated | NFR-SEC-007, NFR-SEC-002, NFR-SEC-004 and the other governance-related NFRs verified by these tests | `levels.list` |
| LEVEL-005 | Regression and smoke: the full automated suite on every pull request (QUAL-008). `tests/test_smoke.py` is the existing smoke test | Yes | Development team | Automated | — | `levels.list` |
| LEVEL-006 | Performance: NFR-PERF-001 (package Ready within 5 minutes) measured from audit-log timestamps over every seed scenario; NFR-PERF-002 (views load in 2 seconds or less) by scripted browser timing; NFR-PERF-003 (at least 10 simultaneously open cases, isolation by case ID checked in the audit log); NFR-PERF-004 (logged model runs reconciled against the audit log and the budget) | Yes | Development team | Automated (scripted) | NFR-PERF-001, NFR-PERF-002, NFR-PERF-003, NFR-PERF-004 | `levels.list` |
| LEVEL-007 | Security and other NFR checks, following each NFR's own Verification Method (secret scan, role-switch tests, fault injection, restart tests, failure injection). The secret scan (NFR-SEC-005) runs locally until the CI workflow exists (QTOOL-006) | Yes | Development team by default; per-module owners are assigned under TEAM-005 (see OQ-003) | Per Verification Method | The NFRs whose Verification Method is one of those listed | `levels.list` |
| LEVEL-008 | User acceptance: demonstration to the business reviewer, scored 4 out of 5 or higher. The Product Owner accepts coverage | Yes | Business reviewer / Product Owner | Manual | NFR-USE-001 | `levels.list` |
| LEVEL-009 | Review and inspection checks that are not executed tests: architecture reviews (NFR-MAINT-001, NFR-MAINT-002), outbound connection configuration review (NFR-SEC-006), interface-conformance review (NFR-COMPAT-002), Chrome and Edge walkthrough (NFR-COMPAT-001), clean-checkout reproduction (NFR-COMPAT-003), and reset plus backup-video review (NFR-AVAIL-002). Each gets a test case with the review evidence as its expected result | Yes | Development team, reviewed by a second team member | Manual | NFR-MAINT-001, NFR-MAINT-002, NFR-SEC-006, NFR-COMPAT-001, NFR-COMPAT-002, NFR-COMPAT-003, NFR-AVAIL-002 | `levels.list` |

**LEVEL-004 negative governance cases:**
- no action without approval;
- stale package version refused;
- only the JobDiva and Workflow agent writes;
- a write requested in sandbox mode is refused and logged, and no write call reaches JobDiva in either mode (NFR-SEC-007, BR-014);
- a startup test per JOBDIVA_MODE, where any value other than mock or sandbox stops the server;
- token never logged;
- duplicates blocked at Received;
- a rejected case stays stopped;
- a returned package needs a new approval;
- restricted visa, sponsorship and FLSA data hidden by role (NFR-SEC-002, BR-011);
- audit log rejects UPDATE and DELETE, tested for both the `audit_writer` and the `coworker_app` role (NFR-SEC-004). `coworker_app` now also holds INSERT, so an action and its audit entry commit in one transaction (NFR-REL-002; Code Standards and Tech Doc v1.2);
- startup refuses a production JobDiva base URL while in mock mode (NFR-COMP-001). `.env.example` defaults `JOBDIVA_BASE_URL` to `https://api.jobdiva.com`, so this case must confirm the mock never calls it;
- model usage cap refuses further calls (TC-004);
- REMINDER_MAX_PER_DAY cap;
- escalation of FLSA, classification, compensation and legal questions.

**Code state (repository at commit efe5b3e; read from the test files, not run for this revision):**
- About 107 test functions in 26 files under `code/tests/`: `unit/` (case states, contracts, mailbox, model client, package, rule lookup, seed mailbox), `governance/` (duplicates, audit, approval, version mismatch, single writer, package flow, rejected case, returned package, vertical slice, local case service), `e2e/test_api.py` and `test_smoke.py`. Tests marked `db` need the local PostgreSQL (`./scripts/start.sh`).
- The planned names of MVP tasks A3 to A7 (audit, duplicates, approval gate, version mismatch, single writer) now exist as tests and are reused, not duplicated. Cases cite the test file and name. A case is "executable today" only when its test exists; anything else is "designed, pending code".
- The CI workflow (`.github/workflows/ci.yml`) does not exist yet. Until it lands, the gate is run locally with `pytest` and `ruff check`.

**Negative governance cases against the tests in the repository:**

| Case | State |
|------|-------|
| No action without approval | Test exists (`test_no_action_without_approval.py`, `test_action_without_approval_is_refused_and_audited`) |
| Stale package version refused | Tests exist (`test_version_mismatch_blocked.py`, `test_action_for_another_version_is_blocked`, API `test_stale_version_returns_409_with_current_version`) |
| Only the JobDiva and Workflow agent writes | Tests exist (`test_only_workflow_server_registers_write_tools`, `test_jobdiva_read_contract_has_no_write_tool`) |
| Duplicates blocked at Received | Tests exist (`test_duplicates_blocked.py`) |
| Rejected case stays stopped; returned package needs a new approval | Tests exist |
| Restricted data hidden by role | Test exists at API level (`test_it_role_does_not_see_restricted_fields`) |
| Audit log append-only | Tests exist (`test_app_role_cannot_change_audit_entries`, `test_audit_writer_role_is_insert_only`) |
| Model usage cap | Tests exist (`test_model_call_refused_after_cap`, `test_cap_is_per_run`) |
| Escalation of FLSA, classification, compensation and legal questions | Partial: `test_package_status_blocked_when_escalated` covers the package status; no test yet for the conflict being raised and escalated |
| Write in sandbox mode refused; startup per JOBDIVA_MODE; invalid value stops the server; production base URL refused | **No test and no implementation yet**: `JOBDIVA_MODE` appears only in `contracts/mcp_tools.py`, and `mcp_servers/mocks/` holds only `outlook` and `teams`. Designed, pending code |
| Token never logged | No test yet (depends on the sandbox connector) |
| REMINDER_MAX_PER_DAY cap | No test yet (belongs to the Should Candidate Follow-up agent) |

---

## 4. Test Environments

| ID | Environment | Purpose | Data Source | Refresh Cadence | Source |
|----|-------------|---------|-------------|------------------|--------|
| ENV-001 | One local environment: PostgreSQL 16 in Docker, all services bound to 127.0.0.1 (INF-001, INF-002) | Development, automated tests, J1 and J2 demo runs and rehearsals | Synthetic seed scenarios in `db/seed`. No connection to client production. No credentials in the repo; `.env.example` holds variable names only | The reset script reloads the seed before each run and demo | `environments.list` |

**Entry check for the environment:** the skeleton builds, ruff is clean, the DB reset script works and the seed scenarios are loaded (see CRIT-001 to CRIT-003).

### 4.1 Dependencies Without a Test Mode

| ID | Dependency | Has Test/Sandbox Mode? | How It Will Be Handled | Source |
|----|------------|-------------------------|--------------------------|--------|
| ENV-002 | JobDiva | A read-only sandbox exists, but it needs API credentials that are not confirmed | Mocked. Sandbox mode is a declared risk, not coverage, and is tested only through negative and startup tests | `environments.list` |
| ENV-003 | Outlook mailbox | No | Mocked | `environments.list` |
| ENV-004 | Teams | No | Mocked | `environments.list` |
| ENV-005 | IT/equipment (Chelsea Tech) | No | Mocked | `environments.list` |
| ENV-006 | Payroll (Paychex) | No | Mocked | `environments.list` |
| ENV-007 | LDC tracker (SharePoint) | No | Mocked | `environments.list` |
| ENV-008 | Knowledge base | No | Mocked | `environments.list` |
| ENV-009 | Model engine (Velocity 2.0 is the delivery method, not a runtime; SAD ADR-006) | No model is needed: `MODEL_PROVIDER=rules` is the default and the factory refuses an unconfigured provider | Agents are tested on the deterministic `rules` engine. A real model engine, if one is approved, must pass the same extraction tests (`test_model_client.py`) before the demo | `environments.list`, SAD ADR-006 |

---

## 5. Test Data Management

| ID | Topic | Value | Source |
|----|-------|-------|--------|
| DATA-001 | Primary data source | Synthetic or anonymized data only (SEC-002, NFR-COMP-001, TC-003). No masked production copy is used, because the system is built from scratch and no production data may be connected | `data.list` |
| DATA-002 | Privacy of restricted data | Restricted data (visa, sponsorship, FLSA) is synthetic and logged by field reference, not by value (BR-011) | `data.list` |
| DATA-003 | Seed scenarios | In `db/seed`. They cover J1 and J2, duplicates, missing and contradictory fields, FLSA conflicts, no bill-back rule, an ambiguous work arrangement and each role | `data.list` |
| DATA-004 | JobDiva sandbox test candidates | If credentials ever arrive, test candidates are created manually by team members in the JobDiva sandbox interface and never by the Coworker (NFR-SEC-007) | `data.list` |
| DATA-005 | Ownership and reset | The development team creates and maintains the seed data and resets it with the reset script before each cycle | `data.list` |
| DATA-006 | Volume | At least 10 simultaneously open cases for the concurrency check (NFR-PERF-003) | `data.list` |
| DATA-007 | Evidence storage | `code/tests/evidence/` | `data.list` |

---

## 6. QA Tooling

> There is no dedicated QA team and no corporate test management tool. The CI gate is listed here as the Answers record places it. Its level-side detail is in LEVEL-005.

| ID | Category | Tool | Status | Source |
|----|----------|------|--------|--------|
| QTOOL-001 | Test case management | Markdown files in the repo (the Test Cases document), with a traceability matrix | No corporate tool | `qtooling.list` |
| QTOOL-002 | QA-level test automation | pytest runs the end-to-end and negative governance tests (QUAL-005). No UI test framework for functional checks this release; functional UI checks are manual. Playwright is used only for navigation timing (NFR-PERF-002) and the automated contrast check (NFR-USE-002) | In use | `qtooling.list` |
| QTOOL-003 | Performance / load testing | A scripted Python timing harness. NFR-PERF-001 uses `time.perf_counter` and audit-log timestamps over every seed scenario. NFR-PERF-002 uses a Playwright navigation-timing script. No load-testing tool, because the demo is single-user on localhost | Scripted, no dedicated tool | `qtooling.list` |
| QTOOL-004 | Defect tracking | GitHub Issues | In use | `qtooling.list` |
| QTOOL-005 | Evidence | Saved in `code/tests/evidence/` | In use | `qtooling.list` |
| QTOOL-006 | CI gate | GitHub Actions running pytest and ruff on every pull request (QUAL-008) | Workflow not in the repo yet. It is an entry prerequisite (CRIT-017) and a declared risk. Fallback: the gate and the secret scan (NFR-SEC-005) are run locally with `pytest`, `ruff check` and a local secret scanner | `qtooling.list` |

---

## 7. Entry & Exit Criteria and Quality Metrics

> Exit thresholds and the 70% coverage target are assumed defaults pending Development and Product Owner confirmation (OQ-001). Line coverage (CRIT-007) is reported and not blocking, because only the skeleton and the case-state tests exist and there is a single test cycle. Every other exit criterion blocks.

| ID | Type | Criterion / Metric | Target or Condition | Source |
|----|------|---------------------|----------------------|--------|
| CRIT-001 | Entry | Skeleton builds | Build succeeds; ruff is clean | `criteria.list` |
| CRIT-002 | Entry | DB reset script and seed data | Reset script works; seed scenarios are loaded | `criteria.list` |
| CRIT-003 | Entry | Developer test suite | Smoke and unit tests pass | `criteria.list` |
| CRIT-004 | Exit | Must cases executed | 100% of Must cases executed (assumed default — see OQ-001) | `criteria.list` |
| CRIT-005 | Exit | Negative governance tests | All green (assumed default — see OQ-001) | `criteria.list` |
| CRIT-006 | Exit | Open critical defects | 0 (assumed default — see OQ-001) | `criteria.list` |
| CRIT-007 | Exit (reported, not blocking) | Line coverage | Target at or above 70% (assumed default, not a confirmed target; TIC-003, QUAL-006 — see OQ-001). A shortfall is logged as a known risk and does not block exit | `criteria.list` |
| CRIT-008 | Exit | J1 and J2 | Pass end to end (assumed default — see OQ-001) | `criteria.list` |
| CRIT-009 | Exit | Demo | Shows at least three agents collaborating on one case (assumed default — see OQ-001) | `criteria.list` |
| CRIT-010 | Exit | Project Definition of Done | Acceptance criteria met; demonstrated end to end on synthetic data; every agent action in the audit log; simulated actions only, with an approval ID for the current package version; acceptance by the Product Owner | `criteria.list` |
| CRIT-011 | Metric | Test pass rate | 100% for negative governance tests; 100% of Must cases executed (assumed default — see OQ-001) | `criteria.list` |
| CRIT-012 | Metric | Package turnaround | 5 minutes or less for every seed scenario (NFR-PERF-001) | `criteria.list` |
| CRIT-013 | Metric | View load time | 2 seconds or less (NFR-PERF-002) | `criteria.list` |
| CRIT-014 | Metric | Line coverage | 70% (assumed default — see OQ-001) | `criteria.list` |
| CRIT-015 | Metric | Open defects by severity at exit | 0 Critical (assumed default — see OQ-001) | `criteria.list` |
| CRIT-016 | Metric | Requirement coverage | Taken from the traceability matrix, with uncovered requirements named | `criteria.list` |
| CRIT-017 | Entry | CI gate | `.github/workflows/ci.yml` exists and runs pytest and ruff on every pull request, or the gate is run locally as the fallback (QTOOL-006) | Review edit, from QTOOL-006 |
| CRIT-018 | Exit | Demo-session rehearsal | At least 3 consecutive error-free runs of J1 and J2 on the presentation machine (NFR-AVAIL-001; TEAM-011) | Review edit, from NFR-AVAIL-001 |
| CRIT-019 | Metric | Defect density | Open defects per Must requirement, reported at exit. No numeric target in a single cycle | Review edit |
| CRIT-020 | Metric | Time to fix | Measured from the Triaged to the Fixed state in GitHub Issues, reported per severity against the fix targets in DEF-001 to DEF-004 | Review edit |

---

## 8. Defect Management

### 8.1 Severity Scale and SLA

| ID | Severity | Definition | Response / Fix SLA | Source |
|----|----------|------------|---------------------|--------|
| DEF-001 | Critical | An inviolable rule is broken (action without approval, a JobDiva write, a leaked secret or restricted data), or J1/J2 is blocked | Fixed before any further testing and before merge | `defects.list` |
| DEF-002 | High | A Must requirement fails with no workaround | Fixed before the demo | `defects.list` |
| DEF-003 | Medium | A Must requirement partially fails or has a workaround; a Should requirement fails | As time allows, or logged as a known issue | `defects.list` |
| DEF-004 | Low | Cosmetic, or Could items | As time allows, or logged as a known issue | `defects.list` |

### 8.2 Lifecycle and Triage

| ID | Topic | Value | Source |
|----|-------|-------|--------|
| DEF-005 | Defect lifecycle states (GitHub Issues) | New → Triaged → In progress → Fixed → Verified → Closed | `defects.list` |
| DEF-006 | Deferred / Won't fix | An alternative end state that needs a written reason and Product Owner confirmation | `defects.list` |
| DEF-007 | Triage responsibility | The development team lead, with the Product Owner confirming priority | `defects.list` |

---

## 9. QA Team, Roles & Schedule

| ID | Topic | Value | Source |
|----|-------|-------|--------|
| TEAM-001 | Who tests | No dedicated QA. The development team tests: Viviana Gomez, Laura Hernandez, David Valdez, Carlos Puerta and Michael Erskin | `team.list` |
| TEAM-002 | Product Owner / BSA | Juan Carlos Giron | `team.list` |
| TEAM-003 | QA lead / coverage acceptor | Proposed: the Product Owner | `team.list` |
| TEAM-004 | Allocation | Not formally set. Testing runs alongside development | `team.list` |
| TEAM-005 | Per-module test owner | To be assigned by the team lead on 2026-10-26 | `team.list` |
| TEAM-006 | Risk and mitigation | The Product Owner is both coverage acceptor and business owner, so there is no independent QA. Mitigation: another team member reviews the traceability matrix before sign-off | `team.list` |
| TEAM-007 | Number of test cycles | One (single cycle) | `team.list` |
| TEAM-008 | Fixed release date | Submission and presentation on 2026-10-28 | `team.list` |
| TEAM-009 | Schedule, 2026-10-26 evening | Entry check and smoke | `team.list` |
| TEAM-010 | Schedule, 2026-10-27 | Execution of the Must cases, defect fixes, re-test | `team.list` |
| TEAM-011 | Schedule, 2026-10-28 morning | Rehearsal of at least 3 consecutive error-free runs of J1 and J2 on the presentation machine (NFR-AVAIL-001), then submission | `team.list` |
| TEAM-012 | Planning basis | The Backlog plans by dates, not sprints, so no sprint-based cycle is derived | `team.list` |

---

## 10. Test Case Conventions

| ID | Topic | Value | Source |
|----|-------|-------|--------|
| TCCONV-001 | Test case ID format | `QC-[MODULE]-[TYPE]-[NNN]`, where TYPE is P (positive), N (negative) or E (edge/boundary). The QC- prefix avoids collision with the TC-001 to TC-005 technical constraints of the Tech Doc | `testcase-conventions.list` |
| TCCONV-002 | Priority scale | High, Medium, Low, aligned with MoSCoW (Must = High, Should = Medium, Could = Low) | `testcase-conventions.list` |
| TCCONV-003 | Module grouping | One code per module, grouped by FRS capability and feature code: ITK, ADQ, VAL, REC, OWN, PKG, GATE, ACT, CASE, AUD, STS, WEB, PRV, plus Should and Could groups if built | `testcase-conventions.list` |
| TCCONV-004 | NFR case grouping | By NFR category: PERF, SEC, AVAIL, USE, REL, MAINT, COMPAT, COMP | `testcase-conventions.list` |
| TCCONV-005 | Required fields per case | Expected-result source (acceptance criterion, requirement text or NFR target); links to SOT IDs (CAP, BR, UR, INT), FR/US/AC IDs and NFR IDs; status of "executable today" or "designed, pending code" | `testcase-conventions.list` |
| TCCONV-006 | Reuse of existing test names | Cases reuse the names of tests that already exist or are planned in the MVP plan | `testcase-conventions.list` |
| TCCONV-007 | Additional required fields | None. No test management tool requires extra fields | `testcase-conventions.list` |

---

## 11. Resolved Inconsistencies Log

| ID | Subject | Options Presented | Resolution Chosen | Resolved By | Date |
|----|---------|--------------------|--------------------|-------------|------|
| — | — | — | — | — | — |

No inconsistencies are recorded in the Answers record for this phase, so there are none to transcribe.

---

## 12. Open Questions

| ID | Subject | Logical Default Applied | Why It's Open |
|----|---------|--------------------------|-----------------|
| OQ-001 | Exit thresholds and the 70% line coverage target | CRIT-004 to CRIT-009, CRIT-011, CRIT-014 and CRIT-015: the thresholds as recorded in §7. The 70% line coverage (TIC-003, QUAL-006) is a reported target and does not block exit. Rationale: the manual context lists them as suggested criteria, not confirmed targets | Awaiting confirmation by Development and the Product Owner |
| OQ-002 | Developer-owned testing levels (unit, integration, system/end-to-end, negative governance, regression/smoke) and the QUAL-001 to QUAL-008 baseline | LEVEL-001 to LEVEL-005, owned by the development team and sourced to Tech Doc §1 and Code Standards §6 | Assumed defaults awaiting Development's confirmation |
| OQ-003 | Owner of security and other NFR checks (LEVEL-007) | The development team, the only testing team on record (TEAM-001), executes each check per the NFR's own Verification Method | The Answers record states the method for each check but not an owner. Awaiting confirmation |
| OQ-004 | Free-text intake without a model | The `rules` engine reads only labelled synthetic emails and chat messages. Tests cover labelled input, conflicting values and instruction-like text (`test_model_client.py`) | Free-form emails need a model engine that is not approved or funded. If one is approved before the demo, its extraction must be tested against the same cases |

---

## 13. Source Inventory

The Answers record does not carry a separate source list. The inventory below lists what the record's own items cite.

| # | Source | Type | Used For |
|---|--------|------|----------|
| 1 | Answers record (`4-quality-context-analysis`) | Resolved Answers record | Sole input to this document: every fact, answer and default |
| 2 | FRS-001 (Functional Requirements Specification) | Upstream document | FR-XXX catalog, Must scope, module codes |
| 3 | NFR Register | Upstream document | NFR-XXX measurable targets and Verification Methods |
| 4 | Tech Doc §1 and Code Standards §6 | Upstream documents | Developer-level baseline QUAL-001 to QUAL-008 |
| 5 | MVP plan (Task 0.1 model client, which replaced the Velocity spike; tasks A3 to A7) | Cited plan | Model client engine; planned test names |
| 6 | `testing-information.json` | Carried-forward facts file | TIC-003 (coverage target) |
| 7 | Manual context | Cited material | Suggested exit criteria and thresholds |
| 8 | Upstream IDs: BR-001, BR-011, BR-014, TC-002 to TC-004, SEC-002, INF-001, INF-002 | Phase 1 and Phase 2 facts | Scope, privacy, environment and governance-test traceability |
| 9 | Upstream files, named because they carry no document ID: `Documents/Velocity/01. Understanding/` (SOT v1.1 offline, functional spec), `Documents/Velocity/02. Architecture/` (nonfunctional-spec, software-architecture-document), `Documents/Velocity/03. Development/` (tech-doc, code-standards), `Documents/Plans/2026-10-26-mvp-implementation-plan.md` | Upstream files | Resolving FRS-001, the NFR Register and the SAD to concrete files |