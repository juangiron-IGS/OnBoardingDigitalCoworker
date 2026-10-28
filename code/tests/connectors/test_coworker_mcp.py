"""The Coworker as an MCP server, for other chat apps (Claude, VS Code). It exposes
intake, answers and status only: decisions stay with people in the web app
(BR-002). Commits to the test database, so each test uses a fresh synthetic person.
"""

import asyncio
import uuid

import pytest

from agents.common.mcp_client import McpToolClient
from mcp_servers.coworker import server as coworker_server

pytestmark = pytest.mark.db

WRITE_OR_DECIDE = {"approve", "reject", "return", "decide", "assign", "execute"}


def _start(person: str) -> str:
    return f"""Candidate ID: {person}
Position: QA Engineer
Hiring manager: Lee Example
Start date: 2026-12-21
Client: Acme Synthetic
Client type: Enterprise
Division: Digital
Line of business: Professional Services
Employment type: W-2
Vendor company: INSPYR Solutions
Work arrangement: Hybrid
Pay rate: 40.00 USD/h
Work city: Los Angeles
Work state: CA
FLSA: Non-exempt
Billing contact: billing.acme@example.com
Equipment: Standard laptop, INSPYR
Sponsorship: No"""


@pytest.fixture
def coworker() -> McpToolClient:
    return McpToolClient(coworker_server.server)


def test_no_tool_can_approve_or_act_on_a_system() -> None:
    names = {t.name for t in asyncio.run(coworker_server.server.list_tools())}

    assert names == {
        "start_onboarding",
        "answer_question",
        "case_status",
        "open_questions",
        "my_alerts",
        "ask_onboarding_knowledge",
    }
    assert not any(word in name for name in names for word in WRITE_OR_DECIDE)


def test_start_answer_and_status_over_mcp(coworker) -> None:
    person = f"SYN-9{uuid.uuid4().int % 10**6:06d}"

    started = coworker.call("start_onboarding", {"text": _start(person)})
    case_id = started["case_id"]
    questions = coworker.call("open_questions", {"case_id": case_id})
    coworker.call("answer_question", {"case_id": case_id, "text": "61.00 USD/h"})
    last = coworker.call("answer_question", {"case_id": case_id, "text": "Lee Example"})
    status = coworker.call("case_status", {"ref": person})

    assert started["state"] == "needs_clarification"
    assert "Bill rate" in started["next_question"]
    assert [q["label"] for q in questions] == ["Bill rate", "Timesheet approver"]
    assert last["state"] == "ready_for_review"
    assert "Ready for review" in status["reply"]


def test_recruiter_alerts_reach_the_mcp_client(coworker) -> None:
    person = f"SYN-9{uuid.uuid4().int % 10**6:06d}"
    case_id = coworker.call("start_onboarding", {"text": _start(person)})["case_id"]

    alerts = coworker.call("my_alerts", {})

    assert any(a["case_id"] == case_id and "Bill rate" in a["text"] for a in alerts)
    assert {a["recipient"] for a in alerts} <= {"Recruiter"}


def test_all_teams_alerts_reach_the_tray(coworker) -> None:
    # The tray's "All teams" choice reads every team's alerts, still read only
    person = f"SYN-9{uuid.uuid4().int % 10**6:06d}"
    coworker.call("start_onboarding", {"text": _start(person)})

    mine = coworker.call("my_alerts", {"limit": 100})
    every = coworker.call("my_alerts", {"limit": 100, "all_teams": True})

    assert {a["recipient"] for a in mine} <= {"Recruiter"}
    assert len(every) >= len(mine)
    assert {a["recipient"] for a in every} <= {
        "Recruiter",
        "Onboarding Team",
        "HR",
        "Onboarding Supervisor",
        "IT",
        "LDC",
    }


def test_unknown_case_is_answered_from_the_record_only(coworker) -> None:
    status = coworker.call("case_status", {"ref": "SYN-NOPE"})

    assert status["reply"].startswith("Information not available")


def test_oversized_text_is_refused(coworker) -> None:
    result = coworker.call("start_onboarding", {"text": "x" * 9000})

    assert result == {"status": "refused", "reason": "text_too_long"}


def test_unknown_role_stops_the_server(monkeypatch) -> None:
    monkeypatch.setenv("COWORKER_MCP_ROLE", "superuser")

    with pytest.raises(ValueError, match="COWORKER_MCP_ROLE"):
        coworker_server.load_role()


def test_knowledge_question_over_mcp(coworker) -> None:
    answer = coworker.call(
        "ask_onboarding_knowledge",
        {"question": "Which forms does a W-2 hire in Texas need?"},
    )

    assert answer["record_id"] == "KB-001"
    assert answer["status"] == "validated"
