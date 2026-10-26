# Dependencies and their licenses

Direct dependencies declared in `code/pyproject.toml`. The versions are those installed and tested on 2026-10-26, and each license is read from the package metadata. The project's own license is in [`LICENSE`](../LICENSE).

## Runtime

| Package | Version tested | License | Used for |
|---|---|---|---|
| fastapi | 0.162.0 | MIT | Web app and API |
| uvicorn | 0.54.0 | BSD-3-Clause | ASGI server for the web app |
| pydantic | 2.14.1 | MIT | Input validation, package lines, rules |
| psycopg (binary, pool) | 3.3.6 | LGPL-3.0-only | PostgreSQL driver, used unmodified as a library |
| mcp | 2.3.0 | MIT | MCP servers (`MCPServer`) |
| PyYAML | 6.0.3 | MIT | Rules catalog (`yaml.safe_load`) |
| httpx | 0.28.1 | BSD-3-Clause | JobDiva sandbox client, read only |

## Development and test

| Package | Version tested | License | Used for |
|---|---|---|---|
| pytest | 9.1.1 | MIT | Test runner |
| pytest-cov | 7.1.0 | MIT | Coverage |
| ruff | 0.17.2 | MIT | Linter and formatter |

## Services and images

| Component | License | Used for |
|---|---|---|
| PostgreSQL 16 (`postgres:16` image) | PostgreSQL License | Case store, audit log and mock stores, in a local container |

No model provider SDK is a dependency: the default model engine (`MODEL_PROVIDER=rules`) uses no model.
