"""Teams mock MCP server: posts alerts to the simulated alerts view. No bot (TC-005)."""

from mcp.server.mcpserver import MCPServer

from mcp_servers.common.db import connect

from .service import AlertsService

server = MCPServer("teams-mock")


@server.tool()
def post_alert(case_id: str, recipient: str, text: str) -> dict:
    """Show an alert to a recipient in the simulated alerts view."""
    with connect() as conn:
        return AlertsService(conn).post_alert(case_id, recipient, text)
