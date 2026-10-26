---
paths:
  - "code/**/*.py"
  - "code/db/**/*.sql"
  - "code/agents/**/prompt.md"
  - "code/agents/**/skills/**"
  - "code/rules/**"
  - "code/scripts/**"
---

# Onboarding Digital Coworker — binding implementation rules

These rules are binding for every plan, implementation and review in `code/`. They condense the approved design. When a rule here and a source document disagree, the source wins, in this order:

1. Checkpoint: `Documents/CheckPoint/14October/checkpoint-deliverable.md`
2. SAD v1.1: `Documents/Velocity/02. Architecture/05. Onboarding Digital Coworker_software-architecture-document.md`
3. Tech Doc v1.1: `Documents/Velocity/03. Development/01. Onboarding Digital Coworker_tech-doc.md` (structure, patterns, commands)
4. Code Standards v1.1: `Documents/Velocity/03. Development/02. Onboarding Digital Coworker_code-standards.md` (style, security, tests, Git)

If a task seems to require breaking a rule marked **non-negotiable**, stop and ask. Do not work around it.

## Stack and structure

- Python 3.12, FastAPI, Pydantic, psycopg 3, PostgreSQL in a local container, pytest, ruff. Agents run on Velocity 2.0. Python and FastAPI remain assumed defaults until the day-one spike confirms them.
- Everything runs on `127.0.0.1`. Never bind to `0.0.0.0`.
- Base branch is `main`. Work on `feature/…` (or `docs/…`) branches and merge through a pull request.
- Folder placement (Tech Doc §5.1):

| Folder | Pattern | Owns |
|---|---|---|
| `web/ui/` | One folder per view, kebab-case files | Chat, simulated inbox, approval, simulated alerts, status |
| `web/api/` | One router per view, thin handlers | Input validation and a call to the case service. No business logic |
| `services/case_service/` | Hexagonal: `domain/`, `application/`, `ports/`, `adapters/` | Case state, package versions, approval gate, rules loader, audit writer |
| `agents/` | One package per agent, plus `common/` | The orchestrator and the Must, Should and Could agents. Each agent folder has `prompt.md` and `skills/` |
| `mcp_servers/` | Shared template: `server.py`, `tools/`, `adapters/`, `guards/` | `jobdiva_read`, `jobdiva_workflow` and the mocks |
| `contracts/` | Signatures only | The case service API and MCP tool signatures shared by both lanes |
| `rules/` | Data only | Rules catalog and templates (YAML, JSON, CSV) |
| `db/` | `migrations/`, `roles/`, `seed/` | Schema, roles and grants, synthetic seed data |

- Lane A (governance core) and Lane B (intelligence and connectors) meet only at `contracts/`. Never import another lane's internals. Changing a contract needs an approval from someone in each lane.

## Governance rules (non-negotiable)

1. **Approval gate (BR-002).** No action on any simulated system without an approval ID for the **current** package version. Any change to a package creates a new version and invalidates earlier approvals. A returned package goes back to Validated. A rejected case stays stopped.
2. **Single writer.** Write tools are registered **only** in `mcp_servers/jobdiva_workflow/`. That server re-verifies the approval ID and package version against the database before every action. It uses an idempotency key built with `contracts.mcp_tools.idempotency_key(approval_id, action)`.
3. **Never write to JobDiva (BR-014, ADR-004)**, in any mode. `jobdiva_read` registers no write tools. `JOBDIVA_MODE` is read once at startup, accepts only `mock` or `sandbox`, and any other value stops the process. A write requested in sandbox mode is refused and audited.
4. **JobDiva token.** It is held in memory only, inside `jobdiva_read`. It never reaches another process, a log, the database or a response.
5. **Audit every agent action.** Every entry records the case, the agent (or human role), the action, the outcome (`completed`, `refused` or `failed`), the rules used (`rule_ids`) and the data used (`data_refs`).
   - An action and its audit entry commit in **one transaction**.
   - The audit table is append-only. `audit_writer` has INSERT only, and `coworker_app` has SELECT only.
   - A refusal is audited before the error reaches the caller.
6. **Restricted data.** Visa, sponsorship and FLSA values are shown only to authorized roles, using the case service's policy decision. In logs, audit entries, prompts and messages they are referenced by field name, never by value. They never appear in messages to leaders or in mass communications.
7. **No legal decisions.** No code or prompt decides or infers FLSA status, worker classification or compensation. These values come from the source field or from HR. A conflict becomes an exception line, escalated to the Onboarding Team.
8. **Duplicates.** The same person with the same start date blocks the case at Received.
9. **Package lines.** Every line carries a label (`source`, `inferred`, `recommended` or `exception`) and its source or rule ID. A line without both is rejected.
10. **Rules are data.** Paperwork, kit, owner, overhead (2% or 5%), bill-back and notification rules live in `rules/` with a rule ID (`R-<domain>-<number>`) and an owner. Never hardcode a business rule in agent or service code.
11. **Synthetic data only.** No real candidate data in seeds, tests, prompts or fixtures. No credentials in the repository. Only `code/.env.example` is committed.
12. **Model budget (TC-004).** Every model call goes through `agents/common/usage_meter.py`, which logs usage per run and per case and enforces `MODEL_USAGE_CAP_PER_RUN`. Use the smaller model for extraction.

## Case states

`Received → Validated (or Needs clarification) → Case set up → Ready for review → Approval gate → Approved / Rejected / returned to Validated → Actions executed`. The Should and Could states (documents, verification, payroll, IGS handoff) follow, then `Closed`. Transitions are data in `services/case_service/domain/case.py`, and any transition not listed there is refused.

## Code patterns

- **Validation:** every request body, MCP tool argument and rules file is validated with a Pydantic model at the boundary, using explicit limits and allow-lists. The API rejects bad input itself, even when the UI also checks.
- **Errors:**
  - Governance refusals extend `GovernanceError(reason)`; for example, `ApprovalRefused` uses `no_approval` or `version_mismatch`.
  - The router for the feature catches the refusal and returns HTTP 409 with `{refused, current_version}`.
  - Bad input returns 400 or 404 with a message naming the field.
  - A 500, an unhandled exception or a stack trace reaching the user is a defect.
- **Failures:** when a dependency fails, the step fails visibly. The case keeps its state, the package status becomes blocked, an alert is shown and the failure is logged with the case ID. A failing Should agent adds an exception line and never stops J1 or J2.
- **Database:**
  - Parameterized queries only.
  - Tables live only in `db/migrations/`; roles and grants only in `db/roles/` (idempotent).
  - `scripts/apply_db.sh` applies migrations, roles and seed data.
  - Never cache approval state or package versions.
- **Logging:** use the shared JSON logging setup with `case_id` on every line. Never log secrets or restricted values.
- **Prompts:** email text, chat text and rule values enter a prompt only inside delimited data sections, never as instructions. Only the JobDiva and Workflow agent's prompt mentions write tools.
- **FastAPI:** use plain `def` for handlers that make blocking calls. Use `async def` only when everything awaited is non-blocking.
- **Front-end:** render dynamic text with `textContent`, never `innerHTML`. The browser talks only to the local API.
- **Style:**
  - Type hints on public functions; `X | None` for optional values.
  - snake_case for modules, functions and variables; PascalCase for classes; UPPER_SNAKE_CASE for constants.
  - Comments only where intent is not obvious, citing the rule, BR or NFR ID.

## Tests (required for "done")

- pytest, named `test_<behavior>`, Arrange-Act-Assert. Mock only at connector boundaries (MCP servers, Velocity model calls), never the approval gate or the case service logic under test.
- Every governance rule above has a negative test in `tests/governance/`. These tests must pass before merge:
  - no action without approval;
  - version mismatch blocked;
  - returned package needs a new approval;
  - only the workflow server writes;
  - duplicates blocked;
  - rejected case stays stopped;
  - no write in sandbox mode;
  - no token in logs;
  - restricted data hidden;
  - every action audited.
- End-to-end tests of J1 and J2 run on the seed scenarios. Line coverage is at least 70%.
- Gates: `ruff check .`, `ruff format --check .` and `pytest --cov=. --cov-fail-under=70`, run from `code/`.

## Scope priority

Build the Must scope first: J1 and J2, the Intake and Validation, Policy and Case Setup, and JobDiva and Workflow agents, the approval gate, the audit log, the JobDiva connectors and mocks, and the governance tests. Should and Could items (Access and Equipment, Candidate Follow-up, Onboarding Knowledge, Culture and Belonging) come only after the MVP works end to end, behind their `FEATURE_*` flags. The demo must show at least three specialized agents collaborating on one case.
