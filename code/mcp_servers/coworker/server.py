"""The Onboarding Coworker as an MCP server, so other chat apps (Claude Desktop,
Claude Code, VS Code) can start onboarding cases, answer the Coworker's questions
and ask for status.

It exposes intake, answers and status only. Approving, returning, rejecting,
assigning an owner and every action on a system stay with people in the web app
(BR-002); this server registers no such tool. It acts as one role
(COWORKER_MCP_ROLE, default recruiter) and goes through the same orchestrator,
governance and audit as the web app. Loopback only.
"""

import os
import sys
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer

from agents.common.model_client import ModelNotConfigured, get_model_client
from agents.orchestrator.chat import status
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.common.db import connect
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.errors import GovernanceError
from services.case_service.domain.privacy import ROLES
from services.case_service.service import LocalCaseService
from web.api.transport import systems

MAX_TEXT = 8000
MAX_REF = 64
# Which simulated alerts each role receives, as in the web app's chat panel.
RECIPIENTS = {
    "recruiter": ["Recruiter"],
    "onboarding": ["Onboarding Team", "HR"],
    "approver": ["Onboarding Supervisor"],
    "it": ["IT"],
}

_catalog = RulesCatalog.load()

server = MCPServer(
    "onboarding-coworker",
    instructions=(
        "The INSPYR Onboarding Coworker. Start an onboarding case from a start email "
        "or message, answer the Coworker's questions about a case, and ask how a case "
        "is going. Approvals and actions on systems are done by people in the "
        "Coworker's web app, not here. Synthetic data only."
    ),
)


def load_role() -> str:
    role = os.environ.get("COWORKER_MCP_ROLE") or "recruiter"
    if role not in ROLES:
        raise ValueError(f"COWORKER_MCP_ROLE must be one of {sorted(ROLES)}")
    return role


def _refused(reason: str) -> dict:
    return {"status": "refused", "reason": reason}


def _run(work):  # noqa: ANN001, ANN202 - a small wrapper for each tool
    """Run one tool on a fresh connection; refusals come back as data."""
    try:
        with connect() as conn:
            wired = systems(os.environ, conn)
            coworker = Orchestrator(
                cases=LocalCaseService(conn, wired.jobdiva),
                model=get_model_client(),
                catalog=_catalog,
                alerts=wired.alerts,
                workflow=wired.workflow,
                jobdiva=wired.jobdiva,
            )
            return work(coworker, conn)
    except GovernanceError as refusal:
        return _refused(refusal.reason)
    except ModelNotConfigured:
        return _refused("model_not_configured")
    except ValueError as error:
        return _refused(str(error))


def _next_question(coworker: Orchestrator, case_id: str | None) -> str | None:
    questions = coworker.questions(case_id) if case_id else []
    if not questions:
        return None
    first = questions[0]
    if first["kind"] == "missing":
        return f"What is the {first['label']}?"
    return f"Two different values were given for {first['label']}. Which one is right?"


@server.tool()
def start_onboarding(text: str, sender: str = "mcp client") -> dict:
    """Start an onboarding case from a new-hire start email or message (synthetic
    data only). Returns the case, its state and the first question to answer."""
    if len(text) > MAX_TEXT:
        return _refused("text_too_long")

    def work(coworker: Orchestrator, _conn) -> dict:  # noqa: ANN001
        result = coworker.process_start(text, source=sender[:120], channel="mcp")
        return {
            **asdict(result),
            "next_question": _next_question(coworker, result.case_id),
        }

    return _run(work)


@server.tool()
def answer_question(case_id: str, text: str) -> dict:
    """Answer the Coworker's next open question about a case."""
    if len(case_id) > MAX_REF or len(text) > MAX_TEXT:
        return _refused("input_too_long")

    def work(coworker: Orchestrator, _conn) -> dict:  # noqa: ANN001
        reply = coworker.chat(text, case_id=case_id)
        return {"reply": reply.reply, "case_id": reply.case_id, "state": reply.state}

    return _run(work)


@server.tool()
def case_status(ref: str) -> dict:
    """How a case is going and who must act, from the case record only. ref is a
    candidate ID (SYN-0043) or a case ID."""
    if len(ref) > MAX_REF:
        return _refused("input_too_long")

    def work(coworker: Orchestrator, _conn) -> dict:  # noqa: ANN001
        reply = status(coworker, ref)
        return {"reply": reply.reply, "case_id": reply.case_id, "state": reply.state}

    return _run(work)


@server.tool()
def open_questions(case_id: str) -> list[dict] | dict:
    """The fields still missing or in conflict for a case, in the order asked."""
    if len(case_id) > MAX_REF:
        return _refused("input_too_long")
    return _run(lambda coworker, _conn: coworker.questions(case_id))


@server.tool()
def my_alerts(limit: int = 20) -> list[dict] | dict:
    """The latest simulated alerts for this server's role. They name fields, never
    FLSA, visa or sponsorship values."""
    recipients = set(RECIPIENTS[load_role()])

    def work(_coworker, conn) -> list[dict]:  # noqa: ANN001
        alerts = AlertsService(conn).list_alerts()
        return [a for a in alerts if a["recipient"] in recipients][
            : max(1, min(limit, 100))
        ]

    return _run(work)


def _load_env_file() -> None:
    """A chat app may start this server without code/.env loaded; read it then,
    without overriding variables that are already set."""
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.split(" #", 1)[0].strip().strip('"'))


def main() -> None:
    _load_env_file()
    load_role()  # an unknown role stops the server at startup
    if "--stdio" in sys.argv:
        server.run(transport="stdio")
        return
    address = urlparse(os.environ.get("COWORKER_MCP_URL", "http://127.0.0.1:8110"))
    server.run(
        transport="streamable-http",
        host=address.hostname or "127.0.0.1",
        port=address.port or 8110,
    )


if __name__ == "__main__":
    main()
