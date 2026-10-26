"""Teams mock MCP server: posts alerts to the simulated alerts view. No bot (TC-005)."""

import os
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer

from mcp_servers.common.db import connect

from .service import AlertsService

server = MCPServer("teams-mock")


@server.tool()
def post_alert(case_id: str, recipient: str, text: str) -> dict:
    """Show an alert to a recipient in the simulated alerts view."""
    with connect() as conn:
        return AlertsService(conn).post_alert(case_id, recipient, text)


def main() -> None:
    address = urlparse(os.environ.get("TEAMS_MOCK_URL", "http://127.0.0.1:8108"))
    server.run(
        transport="streamable-http",
        host=address.hostname or "127.0.0.1",
        port=address.port or 8108,
    )


if __name__ == "__main__":
    main()
