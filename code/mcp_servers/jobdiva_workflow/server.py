"""JobDiva and Workflow MCP server: the only server with write tools (ADR-003).

Every action acts on mock stores only and never reaches JobDiva (BR-014).
"""

import os
from typing import Any
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer

from mcp_servers.common.db import connect
from services.case_service.domain.errors import GovernanceError

from .service import WorkflowService

server = MCPServer(
    "jobdiva-workflow",
    instructions=(
        "Applies approved onboarding actions to simulated systems. Every call needs "
        "the approval ID and package version; the server re-verifies both."
    ),
)


@server.tool()
def execute_simulated_action(
    approval_id: str,
    package_version: int,
    action: str,
    payload: dict[str, Any] | None = None,
) -> dict:
    """Apply one approved action: create_jobdiva_case, create_task_list or
    create_it_request. Refused without an approval for the current package version.
    """
    try:
        with connect() as conn:
            return WorkflowService(conn).execute_simulated_action(
                approval_id, package_version, action, payload or {}
            )
    except GovernanceError as refusal:
        # A refusal is an expected outcome, returned as data so its reason crosses
        # MCP; the service has already audited it.
        return {"status": "refused", "reason": refusal.reason}


def main() -> None:
    address = urlparse(os.environ.get("JOBDIVA_WORKFLOW_URL", "http://127.0.0.1:8106"))
    server.run(
        transport="streamable-http",
        host=address.hostname or "127.0.0.1",
        port=address.port or 8106,
    )


if __name__ == "__main__":
    main()
