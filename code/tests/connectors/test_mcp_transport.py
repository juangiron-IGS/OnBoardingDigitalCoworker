"""Agents reach the systems over MCP (task B4, SAD Alternative B).

The servers run in memory here; at run time the same client reaches them over HTTP.
These tests commit to the test database, so each one uses a fresh synthetic person.
"""

import os
import uuid
from datetime import date

import psycopg
import pytest

from agents.common.mcp_adapters import McpAlerts, McpJobDivaRead, McpJobDivaWorkflow
from agents.common.mcp_client import McpCallFailed, McpToolClient
from contracts.mcp_tools import Alerts, JobDivaRead, JobDivaWorkflow
from mcp_servers.jobdiva_read import server as jobdiva_read_server
from mcp_servers.jobdiva_workflow import server as workflow_server
from mcp_servers.mocks.teams import server as teams_server
from services.case_service.application.create_case import CaseIntake
from services.case_service.domain.case import CaseState
from services.case_service.domain.errors import ApprovalRefused
from services.case_service.domain.package import PackageLine
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db


class NoDuplicates:
    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        return {"found": False, "start_id": None}


@pytest.fixture
def committed_conn():
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        yield conn


@pytest.fixture
def approved(committed_conn) -> tuple[str, str]:
    cases = LocalCaseService(committed_conn, NoDuplicates())
    case_id = cases.create_case(
        CaseIntake(
            person_ref=f"SYN-T{uuid.uuid4().hex[:8]}", start_date=date(2026, 12, 7)
        ),
        agent="intake_validation",
    )
    cases.move_case(case_id, CaseState.VALIDATED, agent="intake_validation")
    cases.move_case(case_id, CaseState.CASE_SET_UP, agent="policy_case_setup")
    cases.build_package(
        case_id,
        [
            PackageLine(
                field="paperwork",
                value="W-4",
                label="recommended",
                source_or_rule_id="R-PA-01",
            )
        ],
        agent="policy_case_setup",
    )
    approval_id = cases.record_approval(
        case_id, package_version=1, approver_role="approver"
    )
    return case_id, approval_id


def _workflow() -> McpJobDivaWorkflow:
    return McpJobDivaWorkflow(McpToolClient(workflow_server.server))


def test_adapters_fulfil_the_contracts() -> None:
    assert isinstance(_workflow(), JobDivaWorkflow)
    assert isinstance(
        McpJobDivaRead(McpToolClient(jobdiva_read_server.server)), JobDivaRead
    )
    assert isinstance(McpAlerts(McpToolClient(teams_server.server)), Alerts)


def test_approved_action_runs_over_mcp(committed_conn, approved) -> None:
    case_id, approval_id = approved

    result = _workflow().execute_simulated_action(
        approval_id, 1, "create_jobdiva_case", {"client": "Acme Synthetic"}
    )

    row = committed_conn.execute(
        "SELECT case_id FROM mocks.jobdiva_cases WHERE approval_id = %s", (approval_id,)
    ).fetchone()
    assert result["status"] == "completed"
    assert row == (case_id,)


def test_refusal_over_mcp_keeps_its_reason(approved) -> None:
    # BR-002 across the process boundary: the reason survives the transport
    _, approval_id = approved

    with pytest.raises(ApprovalRefused) as refusal:
        _workflow().execute_simulated_action(approval_id, 2, "create_task_list", {})
    assert refusal.value.reason == "version_mismatch"


def test_unknown_approval_over_mcp_is_refused() -> None:
    with pytest.raises(ApprovalRefused) as refusal:
        _workflow().execute_simulated_action("apr-nope", 1, "create_task_list", {})
    assert refusal.value.reason == "no_approval"


def test_jobdiva_reads_over_mcp() -> None:
    jobdiva = McpJobDivaRead(McpToolClient(jobdiva_read_server.server))

    duplicate = jobdiva.search_duplicate("SYN-0040", date(2026, 11, 2))
    notes = jobdiva.read_start_notes("JD-START-1042")

    assert duplicate == {"found": True, "start_id": "JD-START-1040"}
    assert notes["work_state"] == "CA"


def test_alert_posted_over_mcp(committed_conn) -> None:
    case_id = f"case-mcp-{uuid.uuid4().hex[:6]}"

    McpAlerts(McpToolClient(teams_server.server)).post_alert(
        case_id, "Recruiter", "Missing: Bill rate."
    )

    row = committed_conn.execute(
        "SELECT recipient, text FROM mocks.alerts WHERE case_id = %s", (case_id,)
    ).fetchone()
    assert row == ("Recruiter", "Missing: Bill rate.")


def test_unreachable_server_fails_visibly() -> None:
    client = McpToolClient("http://127.0.0.1:9/mcp", name="nowhere")

    with pytest.raises(McpCallFailed, match="nowhere"):
        client.call("search_duplicate", {"person_ref": "x", "start_date": "2026-11-02"})
