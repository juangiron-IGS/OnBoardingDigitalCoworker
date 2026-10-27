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
| anthropic | 2.3.0 | Apache-2.0 | Claude engine (`MODEL_PROVIDER=claude`), optional |
| pystray | 0.19.5 | LGPL-3.0 | Coworker Tray icon and Windows notifications (extra `tray`), used unmodified as a library |
| Pillow | 12.3.0 | MIT-CMU | Coworker Tray icon image (extra `tray`) |
| pywebview | 6.2.1 | BSD-3-Clause | Coworker window the tray opens, on Windows' Edge WebView2 (extra `tray`) |
| pythonnet | 3.2.1 | MIT | Installed by pywebview on Windows (extra `tray`) |
| Windows-Toasts | 1.3.1 | Apache-2.0 | Coworker Tray notifications with the Coworker's name, logo and an Open case button (extra `tray`, Windows) |

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
