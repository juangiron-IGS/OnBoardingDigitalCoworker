from datetime import date

from contracts.case_service_api import CaseServiceClient
from contracts.mcp_tools import (
    SIMULATED_ACTIONS,
    JobDivaRead,
    JobDivaWorkflow,
    idempotency_key,
)
from services.case_service.ports.duplicate_search import DuplicateSearch


def test_idempotency_key_is_stable() -> None:
    assert idempotency_key("apr-1", "create_jobdiva_case") == (
        "apr-1:create_jobdiva_case"
    )
    assert idempotency_key("apr-1", "create_jobdiva_case") == idempotency_key(
        "apr-1", "create_jobdiva_case"
    )


def test_idempotency_key_differs_per_action() -> None:
    assert idempotency_key("apr-1", "create_task_list") != idempotency_key(
        "apr-1", "create_jobdiva_case"
    )


def test_simulated_actions_are_the_approved_set() -> None:
    assert (
        frozenset({"create_jobdiva_case", "create_task_list", "create_it_request"})
        == SIMULATED_ACTIONS
    )


class _FakeRead:
    def read_start(self, start_id: str) -> dict:
        return {}

    def read_start_notes(self, start_id: str) -> dict:
        return {}

    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        return {"found": False, "start_id": None}


class _FakeWorkflow:
    def execute_simulated_action(
        self, approval_id: str, package_version: int, action: str, payload: dict
    ) -> dict:
        return {"status": "completed", "key": idempotency_key(approval_id, action)}


def test_jobdiva_read_contract_serves_the_duplicate_port() -> None:
    reader = _FakeRead()
    assert isinstance(reader, JobDivaRead)
    assert isinstance(reader, DuplicateSearch)


def test_jobdiva_read_contract_has_no_write_tool() -> None:
    # BR-014: the read contract exposes reads only
    assert not [
        name
        for name in dir(JobDivaRead)
        if name.startswith(("write", "create", "update", "execute"))
    ]


def test_workflow_contract_is_runtime_checkable() -> None:
    assert isinstance(_FakeWorkflow(), JobDivaWorkflow)


def test_case_service_client_lists_the_governance_operations() -> None:
    expected = {
        "create_case",
        "move_case",
        "build_package",
        "record_approval",
        "return_package",
        "reject_case",
        "case_state",
        "current_package_version",
    }
    assert expected <= set(dir(CaseServiceClient))
