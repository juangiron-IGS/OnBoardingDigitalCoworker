# Velocity 2.0 configuration

Velocity 2.0 is the AI-assisted delivery method the team used to produce this solution, stage by stage (SAD ADR-006). It is not an agent runtime: the agents in `code/agents/` are Python code that reaches a model only through `agents/common/model_client.py`.

This folder links the Velocity stages to what the code implements.

| Velocity stage | Documents | Implemented in |
|---|---|---|
| 01. Understanding | [Source of Truth](../../Documents/Velocity/01.%20Understanding/), Strategic Intake, Functional Specification (FR, BR, UC), Backlog (US) | Acceptance criteria are named in the tests, for example `US-017 AC-001` |
| 02. Architecture | Architecture Source of Truth, NFR Register, quality weights, alternatives, [Software Architecture Document v1.2](../../Documents/Velocity/02.%20Architecture/) | Alternative B: case service, single-writer MCP server, JobDiva READ server, rules as data |
| 03. Development | [Technical Documentation v1.2 and Code Standards v1.1](../../Documents/Velocity/03.%20Development/) | `code/` layout, `pyproject.toml`, the ruff and pytest gates, `.claude/rules/backend-python-coworker.md` |
| Plan | [MVP implementation plan](../../Documents/Plans/2026-10-26-mvp-implementation-plan.md) | Tasks 0.1 to D3, one pull request each |

## Settings the solution reads

Every setting is an environment variable. Names are in [`code/.env.example`](../.env.example), and values go in a local `code/.env` that is never committed. The settings that change the solution's behaviour:

| Variable | Default | Effect |
|---|---|---|
| `MODEL_PROVIDER` | `rules` | Model engine behind the model client. `rules` uses no model and no key |
| `MODEL_USAGE_CAP_PER_RUN` | 50 | Model calls allowed per run (TC-004) |
| `JOBDIVA_MODE` | `mock` | JobDiva READ server mode: `mock` or read-only `sandbox` |
| `WEB_APP_PORT` | 3000 | Port of the web app on `127.0.0.1` |
| `DATABASE_URL`, `AUDIT_DATABASE_URL` | none | PostgreSQL roles: application, and INSERT-only audit |

The `VELOCITY_*` variables come from an earlier assumption that Velocity 2.0 was a runtime (ADR-006). The build does not read them; `.env.example` keeps them commented out in its "Reserved for the pilot" section.
