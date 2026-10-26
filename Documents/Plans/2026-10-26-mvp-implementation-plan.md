# MVP Implementation Plan: Onboarding Digital Coworker (J1 and J2)

> **For the executing agent:** run this plan task by task with the Superpowers `executing-plans` or `subagent-driven-development` skill. Every task follows test-driven development: write the failing test, run it and see it fail, write the minimum code, run it and see it pass, then commit. Binding rules live in `.claude/rules/backend-python-coworker.md`. Read that file before the first task.

**Goal:** demo the two Must journeys end to end by **October 28, 2026**. J1 covers intake and validation. J2 covers the package, approval and simulated actions. At least three specialized agents must collaborate on one case, under the governance rules, using synthetic data only.

**Architecture:** SAD v1.1, Alternative B.
- An Onboarding Orchestrator on Velocity 2.0 routes work to the specialized agents.
- A case service owns state, the approval gate and the audit log in PostgreSQL.
- Each enterprise system is a mock MCP server. Only `jobdiva_workflow` has write tools.
- A FastAPI web app serves the five views.

**Stack:** Python 3.12, FastAPI, Pydantic, psycopg 3, PostgreSQL 16 in Docker, FastMCP, pytest, ruff. All source lives under `code/`, and every command runs from `code/`.

**Sources:**
- Tech Doc v1.1 (structure, code patterns, commands)
- Code Standards v1.1
- Backlog `Documents/Velocity/01. Understanding/04. ...backlog.md` (Must stories and acceptance criteria)
- Checkpoint (demo sequence, seed scenarios)

---

## Scope

### In scope (Must, mapped to tasks)

| Area | User stories | Tasks |
|---|---|---|
| Case states, audit log, duplicates | US-036, US-018, US-017 | A2, A3, A4 |
| Approval gate, decisions, versions | US-012, US-013, US-014 | A5, A6 |
| Single writer, simulated actions, no JobDiva writes | US-015, US-016, US-034, US-035 | A7, B2, B3 |
| Intake (email and chat) and adaptive questions | US-001, US-002, US-003 | B5, B6 |
| Completeness, contradictions, exact-field alerts | US-004, US-005, US-006 | B5 |
| Path, paperwork, kit, owner, FLSA escalation | US-007, US-008, US-009, US-010, US-032 | B4, B7 |
| Package with labels, status and exceptions | US-011, US-033 | A5, B8 |
| Web views and role restriction | US-037, US-038, US-039, US-040, US-019 | C1 to C3 |

### Out of scope until the MVP works end to end

Should and Could items: Access and Equipment, Candidate Follow-up, Onboarding Knowledge, Culture and Belonging, payroll and documents. They stay behind their `FEATURE_*` flags.

There is one exception. If C4 passes before midday on October 27, add Access and Equipment (US-020) as the fourth agent, because it appears in the checkpoint demo.

### Cut line if time runs short

Cut these first, in this order. The demo still holds without them.
1. US-019 (status questions in chat)
2. US-032 (supervisor assigns the owner; keep the recommendation only)
3. US-012 AC-003 (5-minute timing report)
4. US-003 adaptive branching (ask for each missing field once, in a fixed order)

---

## Phase 0 — Gate: Velocity spike (October 26, morning)

### Task 0.1: Confirm Velocity 2.0 can drive our agents

**Goal:** confirm that an agent defined on Velocity 2.0 can:
- call a tool exposed by a local MCP server on `127.0.0.1`;
- return a structured result to Python code.

**Steps:**
1. Write the smallest possible FastMCP server with one tool, `echo(text) -> text`, on `127.0.0.1:8199`.
2. Define one Velocity agent that calls `echo`, then invoke it from a Python script.
3. Record the outcome in `code/velocity/SPIKE.md`:
   - the SDK or API used;
   - how agents and tools are registered;
   - the models available;
   - how model usage is metered.

**Decision:**
- **Pass:** continue with this plan as written.
- **Fail:** switch to the SAD fallback, Alternative A. The mock servers become in-process adapters behind the same `contracts/mcp_tools.py` signatures. Only `agents/common/mcp_client.py` and the start script change, because the tasks below are written against the contracts.

> Every task below depends on Velocity only through `agents/common/velocity_binding.py`. Tests use a fake binding, so lane A never waits for this gate.

---

## Phase 1 — Lane A: governance core (October 26)

### Task A1: Project skeleton

**Files:**
- Create: `code/pyproject.toml`, `code/docker-compose.yml`, `code/scripts/apply_db.sh`, `code/scripts/start.sh`, `code/scripts/reset.sh`, `code/tests/conftest.py`
- Create: the empty packages from Tech Doc §5.1 (`web/`, `services/case_service/{domain,application,ports,adapters}/`, `agents/`, `mcp_servers/`, `contracts/`, `rules/`, `db/{migrations,roles,seed}/`)

**Steps:**
1. Write `pyproject.toml`:
   - `requires-python = ">=3.12"`;
   - dependencies: `fastapi`, `uvicorn`, `pydantic`, `psycopg[binary,pool]`, `mcp`, `pyyaml`;
   - dev dependencies: `pytest`, `pytest-cov`, `ruff`, `httpx`;
   - the ruff configuration from Code Standards §4.2.
2. Copy `docker-compose.yml` and `apply_db.sh` from Tech Doc §8.3 and §4.5.
3. Write `tests/test_smoke.py::test_package_imports`. It imports `services.case_service` and must pass.
4. Run `pip install -e ".[dev]"`, `ruff check .` and `pytest`. Expected: 1 passed.
5. Commit: `Add the code skeleton, tooling and local PostgreSQL`.

### Task A2: Case states (US-036)

**Files:** `services/case_service/domain/case.py`, `services/case_service/domain/errors.py`, `tests/unit/test_case_states.py`

**Steps:**
1. **Failing tests:**
   - `test_allowed_transition_returns_new_state`
   - `test_action_refused_before_approval_gate` (US-036 AC-001)
   - `test_returned_package_goes_back_to_validated` (US-036 AC-002)
   - `test_rejected_case_cannot_move` (US-013 AC-003)
2. Run `pytest tests/unit/test_case_states.py`. Expected: fail, because `CaseState` is not defined.
3. **Implement:**
   - `CaseState` and `ALLOWED`, exactly as in Tech Doc §6.1.
   - `transition(current, target) -> CaseState`, which raises `InvalidTransition(GovernanceError)` for any pair not in `ALLOWED`.
   - `GovernanceError(reason)` and `ApprovalRefused`, as in Code Standards §9.
4. Run the tests. Expected: 4 passed.
5. Commit: `Add case states and governance errors`.

### Task A3: Audit log, schema and writer (US-018)

**Files:**
- Create: `db/migrations/001_audit_log.sql`, `db/migrations/002_cases.sql`, `db/roles/001_roles.sql`
- Create: `services/case_service/ports/audit_log.py`, `services/case_service/adapters/postgres/audit_log.py`
- Test: `tests/governance/test_every_action_is_audited.py`

**Steps:**
1. **Migrations:**
   - `001` holds the `audit_log` table from Tech Doc §4.5.
   - `002` holds `cases`, `package_versions`, `package_lines`, `approvals` and `action_ledger`, following the checkpoint data model. `package_lines.label` has a CHECK constraint on `source`, `inferred`, `recommended` and `exception`. `action_ledger.idempotency_key` is UNIQUE.
   - `001_roles.sql` comes from Tech Doc §4.5.
2. **Failing tests:**
   - `test_completed_action_has_agent_rules_and_data` (US-018 AC-001)
   - `test_refused_action_is_audited` (US-018 AC-002)
   - `test_audit_writer_cannot_update_or_delete`: run UPDATE as `audit_writer` and expect a permission error.
3. Implement the `AuditLog` port and its Postgres adapter, connecting with `AUDIT_DATABASE_URL`.
4. Run `./scripts/reset.sh && pytest tests/governance/test_every_action_is_audited.py`. Expected: 3 passed.
5. Commit: `Add the append-only audit log`.

### Task A4: Case creation and duplicate block (US-017)

**Files:** `services/case_service/application/create_case.py`, `services/case_service/adapters/postgres/case_repository.py`, `tests/governance/test_duplicates_blocked.py`

**Steps:**
1. **Failing tests:**
   - `test_second_start_same_person_and_date_is_blocked_at_received` (AC-001)
   - `test_block_message_names_existing_case` (AC-002)
   - `test_duplicate_found_in_jobdiva_also_blocks`: a fake `jobdiva_read` returns found.
2. **Implement:** `create_case(repo, audit, jobdiva_read, intake)`.
   - It checks the case store first, then `jobdiva_read.search_duplicate`.
   - On a duplicate it raises `DuplicateCase(existing_case_id)` and audits the refusal.
   - Otherwise it inserts the case in `Received` and audits `create_case`.
3. Run the tests. Expected: pass.
4. Commit: `Create cases and block duplicates`.

### Task A5: Package versions and the approval gate (US-011, US-012, US-013, US-014, US-033)

**Files:** `services/case_service/domain/package.py`, `services/case_service/domain/approval_gate.py`, `services/case_service/application/{build_package,record_approval,return_package,reject_case}.py`

**Tests:** in `tests/governance/`:
- `test_no_action_without_approval.py`
- `test_version_mismatch_blocked.py`
- `test_returned_package_needs_new_approval.py`
- `test_rejected_case_stays_stopped.py`

and `tests/unit/test_package.py`.

**Steps:**
1. **Failing tests:**
   - `test_package_line_requires_label_and_source` (US-011 AC-002)
   - `test_no_package_for_failing_case` (US-011 AC-003)
   - `test_change_creates_new_version_and_keeps_old` (US-012 AC-002)
   - `test_approval_records_approver_time_version_and_id` (US-014 AC-001)
   - `test_return_or_reject_issues_no_approval_id` (US-014 AC-002)
   - `test_package_status_blocked_when_flsa_escalated` (US-033 AC-001)
   - `test_package_status_needs_clarification_when_waiting` (US-033 AC-002)
   - plus the four governance files above (examples in Tech Doc §6.1 and §7.4).
2. **Implement:**
   - `PackageLine` is a Pydantic model whose label is one of the four values and which requires `source_or_rule_id`.
   - `approval_gate.verify` follows Tech Doc §6.1.
   - Approval, return and reject each write their state change and audit entry in one transaction.
   - Package status is derived as `ready`, `blocked` or `needs_clarification`.
3. Run `pytest tests/unit tests/governance`. Expected: pass.
4. Commit: `Add package versions and the approval gate`.

### Task A6: Contracts (unblocks lane B)

**Files:** `contracts/case_service_api.py`, `contracts/mcp_tools.py`

**Steps:**
1. Write the `CaseServiceClient` protocol, with exactly the operations A2 to A5 expose, and the MCP tool signatures:
   - `read_start`, `read_start_notes`, `search_duplicate`;
   - `execute_simulated_action(approval_id, package_version, action)`;
   - `idempotency_key()`.
2. Write `tests/unit/test_contracts.py::test_idempotency_key_is_stable`.
3. Commit, then push so lane B can build against it: `Define the case service and MCP tool contracts`.

> **After this task**, changing a contract needs an approval from someone in each lane.

### Task A7: Single writer server (US-015, US-016, US-034)

**Files:** `mcp_servers/common/server_template.py`, `mcp_servers/jobdiva_workflow/{server.py,guards/approval.py,ledger.py}`

**Tests:** in `tests/governance/`:
- `test_only_workflow_agent_writes.py`
- `test_no_action_without_approval.py`, extended to the server

**Steps:**
1. **Failing tests:**
   - `test_action_without_approval_id_refused` (US-015 AC-001)
   - `test_action_carries_approval_id` (US-015 AC-002)
   - `test_action_for_newer_version_blocked` (US-015 AC-003)
   - `test_retry_with_same_key_does_not_duplicate`
   - `test_only_workflow_server_registers_write_tools`: scan every server's registered tools.
2. **Implement** `execute_simulated_action` as in Tech Doc §6.1. It re-verifies against the database and applies the action and its audit entry in one transaction.
   - Actions: `create_jobdiva_case`, `create_task_list`, `create_it_request`.
   - They write to the mock stores, in their own schema.
3. Run the tests. Expected: pass.
4. Commit: `Add the single-writer JobDiva and Workflow server`.

---

## Phase 2 — Lane B: connectors, rules and agents (October 26 afternoon to October 27)

Lane B starts from the A6 contracts. Until A3 to A5 merge, it uses fakes of `CaseServiceClient`.

### Task B1: Seed scenarios and the rules catalog

**Files:** `db/seed/001_scenarios.sql`, `db/seed/mailbox/*.eml`, `rules/paperwork/*.yaml`, `rules/kit/*.yaml`, `rules/owners/*.yaml`, `rules/notifications/*.yaml`, `rules/templates/*`

**Steps:**
1. **Synthetic scenarios** (from the checkpoint):
   - `complete_and_consistent` (W-2, California)
   - `missing_two_fields`: the main demo case, with 2 missing fields
   - `duplicate`
   - `work_arrangement_contradiction`
   - `flsa_conflict` (corp-to-corp, Texas, no state forms)
   - `client_without_billback`
2. **Rules:**
   - paperwork by contract type, FLSA, state, city and client. Include `R-PA-02`, plus California, Philadelphia and Texas.
   - kit by contract type;
   - owner by client type and role;
   - 2% and 5% overhead.

   Every rule has an `id`, an `owner` and a `version`.
3. Test `tests/unit/test_rule_lookup.py`:
   - `test_lookup_returns_rule_with_its_id`
   - `test_rule_shows_owner_and_version` (US-007 AC-003)
   - `test_no_kit_rule_returns_none` (US-008 AC-002)
4. Implement the rules loader in `services/case_service/adapters/rules_files/`, using `yaml.safe_load`.
5. Commit: `Add synthetic seed scenarios and the rules catalog`.

### Task B2: JobDiva READ server (US-035)

**Files:** `mcp_servers/jobdiva_read/{server.py,config.py,adapters/mock.py,adapters/sandbox.py}`

**Tests:**
- `tests/connectors/test_jobdiva_read_mock.py`
- `tests/governance/test_no_write_in_sandbox_mode.py`
- `tests/governance/test_no_token_in_logs.py`

**Steps:**
1. **Failing tests:**
   - `test_mock_is_default_mode` (AC-001)
   - `test_invalid_mode_stops_process`
   - `test_read_server_registers_no_write_tools`
   - `test_write_in_sandbox_refused_and_logged` (AC-002)
   - `test_token_never_appears_in_logs` (AC-003)
2. **Implement** `config.py` as in Tech Doc §6.1. The mock adapter reads the seed data. The sandbox adapter does read-only HTTP and keeps the token in memory.
3. Run the tests. Expected: pass.
4. Commit: `Add the JobDiva READ server in mock and read-only sandbox mode`.

### Task B3: Other mock MCP servers

**Files:** `mcp_servers/mocks/{outlook,teams,chelsea_tech,paychex,ldc_tracker,knowledge_base}/server.py`

**Steps:**
1. Build each server from the shared template, with read tools only.
   - `outlook` lists and reads synthetic `.eml` files.
   - `teams` posts to the simulated alerts store.
2. Test `tests/connectors/test_mock_servers.py`, one read test per server.
3. Commit: `Add the remaining mock MCP servers`.

> **Time saver:** for the MVP, only `outlook` and `teams` are required. Create the others as stubs with one read tool each.

### Task B4: Velocity binding, usage meter and notifications

**Files:** `agents/common/{velocity_binding.py,usage_meter.py,mcp_client.py,case_context.py,notifications.py}`

**Steps:**
1. **Failing tests:**
   - `test_model_call_refused_after_cap` (TC-004)
   - `test_usage_logged_per_run_and_case`
   - `test_leader_message_never_contains_restricted_values` (US-040 AC-003)
2. **Implement:**
   - `velocity_binding` uses the API confirmed in Task 0.1, plus a `FakeBinding` for tests.
   - `notifications` renders templates per audience from `rules/templates/` and posts through the Teams or Outlook mock.
3. Commit: `Add the Velocity binding, usage meter and notifications tool`.

### Task B5: Intake and Validation agent (US-001, US-002, US-004, US-005, US-006)

**Files:** `agents/intake_validation/{agent.py,prompt.md,skills/}`, `tests/unit/test_intake_validation.py`

**Steps:**
1. **Failing tests**, each on a seed scenario:
   - `test_email_creates_case_with_start_data` (US-001 AC-001)
   - `test_ambiguous_value_not_confirmed` (US-001 AC-002)
   - `test_blank_start_notes_reports_six_fields_by_name` (US-004 AC-001)
   - `test_missing_manager_moves_case_to_needs_clarification` (US-004 AC-002)
   - `test_contradiction_lists_both_values_and_sources` (US-005 AC-001, AC-002)
   - `test_alert_names_exact_field_and_is_audited` (US-006 AC-001, AC-002)
2. **Implement:**
   - The model is used only for field extraction from email or chat text, through the binding and with the smaller model.
   - Completeness and contradiction checks are plain Python over the extracted fields. They are deterministic and testable without a model.
   - `prompt.md` delimits the email text as data.
3. Commit: `Add the Intake and Validation agent`.

### Task B6: Adaptive questions (US-003)

**Steps:**
1. **Failing tests:**
   - `test_confirmed_value_not_asked_again`
   - `test_single_work_arrangement_used_everywhere`
2. Implement the question queue: missing fields first, then contradictions, with confirmed values locked.
3. Commit: `Ask only for missing or contradictory values`.

### Task B7: Policy and Case Setup agent (US-007, US-008, US-009, US-010, US-032)

**Files:** `agents/policy_case_setup/{agent.py,prompt.md,skills/}`

**Steps:**
1. **Failing tests:**
   - `test_paperwork_lists_each_form_with_rule_id` (US-007 AC-002)
   - `test_no_recommendation_for_incomplete_case` (US-007 AC-004)
   - `test_kit_matches_contract_type` (US-008 AC-001)
   - `test_flsa_conflict_escalated_and_no_value_chosen` (US-009)
   - `test_owner_recommended_pending_assignment` (US-010 AC-002)
   - `test_supervisor_assignment_replaces_recommendation_and_is_logged` (US-032)
2. **Implement** rule lookups only. The agent never computes or decides FLSA, classification or compensation. A conflict becomes an `exception` line.
3. Commit: `Add the Policy and Case Setup agent`.

### Task B8: JobDiva and Workflow agent and the Orchestrator (US-011, US-015, US-034, AC8)

**Files:** `agents/jobdiva_workflow/`, `agents/orchestrator/`

**Steps:**
1. **Failing tests:**
   - `test_orchestrator_routes_intake_then_policy_then_package`
   - `test_package_built_after_last_answer`
   - `test_only_workflow_agent_calls_write_tools`
   - `test_approved_case_creates_jobdiva_case_tasks_with_approval_id` (US-034 AC-003)
2. **Implement:**
   - The orchestrator owns the case flow: intake, validation (with questions), case setup, package, approval gate, then actions.
   - The workflow agent calls only `jobdiva_workflow`, passing the approval ID, package version and idempotency key.
3. Commit: `Add the orchestrator and the JobDiva and Workflow agent`.

---

## Phase 3 — Lane C: web app and demo (October 27)

### Task C1: API routers and role selector (US-040)

**Files:** `web/api/{main.py,deps.py,routers/{chat,inbox,approvals,alerts,status}.py}`

**Steps:**
1. **Failing tests:**
   - `test_it_role_does_not_see_visa_sponsorship_flsa` (US-040 AC-001)
   - `test_onboarding_role_sees_restricted_fields` (US-040 AC-002)
   - `test_stale_version_returns_409_with_current_version`
   - `test_bad_input_returns_400_naming_field`
2. **Implement thin routers.** The role comes from the simulated selector, and the case service applies the policy decision.
3. Commit: `Add the API routers`.

### Task C2: The five views (US-037, US-038, US-039)

**Files:** `web/ui/index.html`, `web/ui/shared/*`, `web/ui/views/{chat,simulated-inbox,approval,simulated-alerts,status}/`

**Steps:**
1. **Build the views:**
   - The inbox has a "new email" button.
   - The approval view shows every line with its label and source, and lists exceptions before the decision buttons. The buttons are disabled when no package is ready.
   - The alerts view shows each alert's recipient and text.
   - The status view shows the JobDiva mock case, the requests and the audit log.
   - Render text with `textContent` only.
2. Verify headless with Playwright on the demo scenario.
3. Commit: `Add the five web views`.

### Task C3: Status in chat (US-019, cuttable)

**Steps:**
1. **Failing tests:**
   - `test_status_answer_names_state_and_who_must_act`
   - `test_unknown_item_reports_not_available`
2. Implement it from the case record and the audit log. The answer comes from data, not from a model guess.
3. Commit: `Answer case status questions in chat`.

### Task C4: End-to-end demo

**File:** `tests/e2e/test_demo_sequence.py`

**Steps:**
1. **Tests:**
   - `test_j1_missing_two_fields_then_ready_package`
   - `test_j2_approve_v2_creates_mock_case_with_approval_id`
   - `test_duplicate_blocked_end_to_end`
   - `test_three_agents_collaborate_on_one_case`: the audit log shows Intake, Policy and JobDiva and Workflow on the same `case_id`.
2. Run the full suite with `pytest --cov=. --cov-fail-under=70`, `ruff check .` and `ruff format --check .`.
3. Commit: `Add the end-to-end demo tests`.

> **Checkpoint, October 27 at midday:** if C4 does not pass, freeze every Should and Could item and apply the cut line.

---

## Phase 4 — Hardening and submission (October 28)

### Task D1: Start, health check and reset

1. `start.sh`, `health_check.py` and `reset.sh` as described in Tech Doc §4.4.
2. Run a dry run from a clean clone on a second machine.

### Task D2: Submission package

1. Fill in the *Planned* sections of the README: install, run, demo, configuration and known limitations.
2. Add `LICENSE` and the dependency list.
3. Add `Documents/Submission/`: architecture diagram, final presentation and the backup demo video (or its link).
4. Save test evidence in `code/tests/evidence/`, including the pytest and coverage reports.
5. Add the Velocity configuration in `code/velocity/`, and each agent's prompts and skills in its folder.

### Task D3: Record the backup video

Record the demo sequence on the seed data:
1. Recruiter sends the start.
2. Two fields are missing.
3. Recruiter answers.
4. Policy applies `R-PA-02`.
5. Package v2 is approved.
6. The mock case is created with its approval ID.
7. Audit log and alerts.

---

## Parallel execution

| Who | October 26 | October 27 | October 28 |
|---|---|---|---|
| Lane A (2 people) | 0.1, then A1 to A7 | Support B8 and C1, fix review findings | D1 |
| Lane B (2 to 3 people) | B1, B2, B3 (against contracts) | B4 to B8 | D2 |
| Lane C (1 to 2 people) | C2 view scaffolding | C1, C2, C3, C4 | D2, D3 |

Merge to `main` through one PR per task or small group of tasks. Run `code-review-auto` and `/security-review` on every PR that touches the approval gate, `jobdiva_workflow`, the audit writer or the contracts.

## Open questions (do not block the plan)

| # | Question | Default used until answered |
|---|---|---|
| 1 | Velocity SDK and tool-calling mechanism | Settled by Task 0.1 |
| 2 | Authorized roles for restricted data (OQ-003) | Onboarding Team and Approver see them. Recruiter, IT and leaders do not |
| 3 | Unit of `MODEL_USAGE_CAP_PER_RUN` | Number of model calls per run |
| 4 | Exact demo text of the alert messages | Taken from `rules/templates/`, reviewed by the PO before recording |
