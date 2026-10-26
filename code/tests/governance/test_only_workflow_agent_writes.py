import asyncio
import importlib
from pathlib import Path

import pytest

from contracts.mcp_tools import JobDivaWorkflow
from mcp_servers.jobdiva_workflow.service import WorkflowService
from services.case_service.domain.errors import ApprovalRefused, GovernanceError

SERVERS_ROOT = Path(__file__).resolve().parents[2] / "mcp_servers"
WRITE_PREFIXES = ("execute", "create", "write", "update", "delete", "post_order")


def _server_modules() -> list[str]:
    return [
        ".".join(path.relative_to(SERVERS_ROOT.parent).with_suffix("").parts)
        for path in SERVERS_ROOT.rglob("server.py")
    ]


def test_only_workflow_server_registers_write_tools() -> None:
    # Single writer: write tools exist only in mcp_servers/jobdiva_workflow
    modules = _server_modules()
    assert "mcp_servers.jobdiva_workflow.server" in modules

    for name in modules:
        server = importlib.import_module(name).server
        tools = [tool.name for tool in asyncio.run(server.list_tools())]
        writes = [tool for tool in tools if tool.startswith(WRITE_PREFIXES)]
        if name == "mcp_servers.jobdiva_workflow.server":
            assert writes == ["execute_simulated_action"]
        else:
            assert writes == [], f"{name} registers write tools {writes}"


@pytest.mark.db
def test_workflow_service_fulfils_the_contract(app_conn) -> None:
    assert isinstance(WorkflowService(app_conn), JobDivaWorkflow)


@pytest.mark.db
def test_action_without_approval_is_refused_and_audited(app_conn) -> None:
    # US-015 AC-001
    with pytest.raises(ApprovalRefused) as refusal:
        WorkflowService(app_conn).execute_simulated_action(
            "apr-unknown", 1, "create_jobdiva_case", {}
        )

    outcome = app_conn.execute(
        "SELECT outcome FROM audit_log"
        " WHERE approval_id = 'apr-unknown' AND agent = 'jobdiva_workflow'"
    ).fetchone()[0]
    assert refusal.value.reason == "no_approval"
    assert outcome == "refused"


@pytest.mark.db
def test_action_carries_the_approval_id(app_conn, approved_case) -> None:
    # US-015 AC-002, US-034 AC-003
    case_id, approval_id = approved_case

    result = WorkflowService(app_conn).execute_simulated_action(
        approval_id, 1, "create_jobdiva_case", {"client": "Acme Synthetic"}
    )

    record = app_conn.execute(
        "SELECT case_id, approval_id FROM mocks.jobdiva_cases WHERE approval_id = %s",
        (approval_id,),
    ).fetchone()
    entry = app_conn.execute(
        "SELECT agent, outcome, approval_id, package_version FROM audit_log"
        " WHERE case_id = %s AND action = 'create_jobdiva_case'",
        (case_id,),
    ).fetchone()
    assert result["status"] == "completed"
    assert record == (case_id, approval_id)
    assert entry == ("jobdiva_workflow", "completed", approval_id, 1)


@pytest.mark.db
def test_action_for_another_version_is_blocked(app_conn, approved_case) -> None:
    # US-015 AC-003
    _, approval_id = approved_case

    with pytest.raises(ApprovalRefused) as refusal:
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 2, "create_task_list", {}
        )
    assert refusal.value.reason == "version_mismatch"


@pytest.mark.db
def test_retry_with_same_key_does_not_duplicate(app_conn, approved_case) -> None:
    # NFR-REL-005: retrying a completed action does not repeat it
    _, approval_id = approved_case
    workflow = WorkflowService(app_conn)

    workflow.execute_simulated_action(approval_id, 1, "create_task_list", {})
    retry = workflow.execute_simulated_action(approval_id, 1, "create_task_list", {})

    count = app_conn.execute(
        "SELECT count(*) FROM mocks.task_lists WHERE approval_id = %s", (approval_id,)
    ).fetchone()[0]
    assert retry["status"] == "already_completed"
    assert count == 1


@pytest.mark.db
def test_unknown_action_is_refused(app_conn, approved_case) -> None:
    _, approval_id = approved_case

    with pytest.raises(GovernanceError) as refusal:
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 1, "place_laptop_order", {}
        )
    assert refusal.value.reason == "unknown_action"
