"""JobDiva READ MCP server: start, start notes and duplicate search. No write tools
(BR-014). The mode is fixed at startup; the sandbox token stays in this process."""

import os
from datetime import date
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer

from .adapters.mock import MockJobDiva
from .adapters.sandbox import SandboxJobDiva
from .config import load_mode

MODE = load_mode(os.environ)


def _connector() -> MockJobDiva | SandboxJobDiva:
    if MODE == "mock":
        return MockJobDiva()
    return SandboxJobDiva(
        base_url=os.environ["JOBDIVA_BASE_URL"],
        client_id=os.environ["JOBDIVA_CLIENT_ID"],
        api_user=os.environ["JOBDIVA_API_USER"],
        api_password=os.environ["JOBDIVA_API_PASSWORD"],
    )


_jobdiva = _connector()
server = MCPServer(
    "jobdiva-read",
    instructions=f"Reads JobDiva starts in {MODE} mode. It has no write tools.",
)


@server.tool()
def read_start(start_id: str) -> dict:
    """Read one start by its JobDiva start ID."""
    return _jobdiva.read_start(start_id)


@server.tool()
def read_start_notes(start_id: str) -> dict:
    """Read the recruiter notes of one start."""
    return _jobdiva.read_start_notes(start_id)


@server.tool()
def search_duplicate(person_ref: str, start_date: str) -> dict:
    """Is there already an onboarding for this person and start date (YYYY-MM-DD)?"""
    return _jobdiva.search_duplicate(person_ref, date.fromisoformat(start_date))


def main() -> None:
    address = urlparse(os.environ.get("JOBDIVA_MOCK_URL", "http://127.0.0.1:8101"))
    server.run(
        transport="streamable-http",
        host=address.hostname or "127.0.0.1",
        port=address.port or 8101,
    )


if __name__ == "__main__":
    main()
