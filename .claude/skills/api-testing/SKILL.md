---
name: api-testing
description: Writing or fixing tests of the Coworker's HTTP API (FastAPI under /api) and its MCP servers. Use when a case checks an endpoint, a status code, a role restriction, an error body or an MCP tool. Uses FastAPI TestClient and pytest, not Playwright.
---

# API Testing (FastAPI and MCP)

Standard: Arrange-Act-Assert, one criterion per test, contract before values. This project uses pytest, not Playwright.

How to apply in this repo:
- HTTP tests live in `code/tests/e2e/test_api.py`. Copy its pattern: a `client` fixture that overrides `web.api.deps.get_conn` with the rolled-back `app_conn`, `TestClient(app)`, `pytestmark = pytest.mark.db`, and the role sent in the `X-Role` header (`recruiter` and the others; read `web/api/deps.py` for the real role names).
- MCP tests: `tests/connectors/` (tool surface and refusals) and `tests/e2e/test_over_mcp.py` (agents over HTTP). The Coworker MCP server must expose no tool that approves, returns, rejects, assigns or acts on a system.
- Order of assertions: status code, response shape, business values, side effects (case state, audit-log row, alert). Negative cases are mandatory: wrong role, stale package version, missing approval ID, duplicate, oversized text, unknown case.
- Name each test after what it proves and add its name to the `QC-` case ("Automated by") through `test-cases-maintenance`.
- Read the router in `web/api/routers/` before writing the test (`cases`, `inbox`, `knowledge`, `health`, and the others); do not assume a route.
- Tests never reach a real JobDiva or a real model: `conftest.py` forces mock, rules and in-process transport.
