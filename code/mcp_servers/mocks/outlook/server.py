"""Outlook mailbox mock MCP server: reads synthetic start emails. No write tools."""

from mcp.server.mcpserver import MCPServer

from .service import MailboxService

server = MCPServer("outlook-mock")
_mailbox = MailboxService()


@server.tool()
def list_messages() -> list[dict]:
    """List the synthetic start emails in the onboarding mailbox."""
    return _mailbox.list_messages()


@server.tool()
def read_message(message_id: str) -> dict:
    """Read one synthetic start email by its ID."""
    return _mailbox.read_message(message_id)
