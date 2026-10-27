"""Knowledge base mock MCP server (US-025): searchKnowledge, validateKnowledge and
registerUnresolved from the checkpoint's knowledge module. Loopback only."""

import os
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer

from mcp_servers.common.db import connect

from .service import KnowledgeService

server = MCPServer("knowledge-mock")


@server.tool()
def list_records() -> list[dict]:
    """Every knowledge record with its current status."""
    with connect() as conn:
        return KnowledgeService(conn).records()


@server.tool()
def validate_record(record_id: str, decision: str, decided_by: str) -> dict:
    """Record the Onboarding Team's decision (validated or rejected) on a record."""
    with connect() as conn:
        try:
            KnowledgeService(conn).validate(record_id, decision, decided_by=decided_by)
        except KeyError:
            return {"status": "refused", "reason": "unknown_record"}
        except ValueError:
            return {"status": "refused", "reason": "bad_decision"}
    return {"record_id": record_id, "status": decision}


@server.tool()
def register_unresolved(question: str, asked_by: str, channel: str, reason: str) -> str:
    """Keep a question no record answers pending for the Onboarding Team."""
    with connect() as conn:
        return KnowledgeService(conn).register_unresolved(
            question[:1000], asked_by=asked_by, channel=channel, reason=reason
        )


@server.tool()
def log_answer(
    record_id: str, status: str, channel: str, matched_by: str = "words"
) -> dict:
    """Audit an answer given from a record, and how the record was chosen."""
    with connect() as conn:
        KnowledgeService(conn).log_answer(
            record_id, status, channel=channel, matched_by=matched_by[:20]
        )
    return {"logged": record_id}


@server.tool()
def pending_questions() -> list[dict]:
    """The questions pending for the Onboarding Team, newest first."""
    with connect() as conn:
        return KnowledgeService(conn).pending()


def main() -> None:
    address = urlparse(
        os.environ.get("KNOWLEDGE_BASE_MOCK_URL", "http://127.0.0.1:8109")
    )
    server.run(
        transport="streamable-http",
        host=address.hostname or "127.0.0.1",
        port=address.port or 8109,
    )


if __name__ == "__main__":
    main()
