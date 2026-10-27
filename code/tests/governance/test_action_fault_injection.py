"""Single writer under faults: an action and its audit entry are saved together, and
a retry after a failure repeats nothing (NFR-REL-002, NFR-REL-005).

Cases: QC-REL-E-002 and QC-REL-E-004.
"""

import pytest

from mcp_servers.jobdiva_workflow.service import WorkflowService
from services.case_service.adapters.postgres.audit_log import PostgresAuditLog


def _count(conn, table: str, approval_id: str) -> int:
    return conn.execute(
        f"SELECT count(*) FROM mocks.{table} WHERE approval_id = %s",  # noqa: S608
        (approval_id,),
    ).fetchone()[0]


def _ledger(conn, approval_id: str) -> int:
    return conn.execute(
        "SELECT count(*) FROM action_ledger WHERE approval_id = %s", (approval_id,)
    ).fetchone()[0]


def _completed_audit(conn, case_id: str, action: str) -> int:
    return conn.execute(
        "SELECT count(*) FROM audit_log"
        " WHERE case_id = %s AND action = %s AND outcome = 'completed'",
        (case_id, action),
    ).fetchone()[0]


@pytest.mark.db
def test_fault_before_the_audit_entry_leaves_no_action_behind(
    app_conn, approved_case, monkeypatch
) -> None:
    # QC-REL-E-002 step 1: inject a fault between the state write and the audit write
    case_id, approval_id = approved_case
    original = PostgresAuditLog.append

    def fail_on_completion(self, **entry):
        if entry.get("outcome") == "completed":
            raise RuntimeError("injected fault before the audit entry")
        return original(self, **entry)

    monkeypatch.setattr(PostgresAuditLog, "append", fail_on_completion)

    with pytest.raises(RuntimeError, match="injected fault"):
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 1, "create_task_list", {}
        )

    # QC-REL-E-002 step 2: neither the record, nor the ledger, nor the audit remains
    assert _count(app_conn, "task_lists", approval_id) == 0
    assert _ledger(app_conn, approval_id) == 0
    assert _completed_audit(app_conn, case_id, "create_task_list") == 0


@pytest.mark.db
def test_fault_after_the_state_write_leaves_no_audit_entry_behind(
    app_conn, approved_case, monkeypatch
) -> None:
    # QC-REL-E-002: the other direction, a fault right after the record is written
    case_id, approval_id = approved_case
    original = WorkflowService._apply

    def apply_then_fail(self, action, case_id, approval_id, payload):
        original(self, action, case_id, approval_id, payload)
        raise RuntimeError("injected fault after the state write")

    monkeypatch.setattr(WorkflowService, "_apply", apply_then_fail)

    with pytest.raises(RuntimeError, match="injected fault"):
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 1, "create_jobdiva_case", {"client": "Acme Synthetic"}
        )

    assert _count(app_conn, "jobdiva_cases", approval_id) == 0
    assert _completed_audit(app_conn, case_id, "create_jobdiva_case") == 0


@pytest.mark.db
def test_retry_after_a_failed_second_action_duplicates_nothing(
    app_conn, approved_case, monkeypatch
) -> None:
    # QC-REL-E-004 step 1: fail the second of several approved actions, then retry
    case_id, approval_id = approved_case
    workflow = WorkflowService(app_conn)
    original = WorkflowService._apply
    failures = {"left": 1}

    def fail_second_action_once(self, action, case_id, approval_id, payload):
        if action == "create_task_list" and failures["left"]:
            failures["left"] -= 1
            raise RuntimeError("injected fault on the second action")
        return original(self, action, case_id, approval_id, payload)

    monkeypatch.setattr(WorkflowService, "_apply", fail_second_action_once)
    actions = [
        ("create_jobdiva_case", {"client": "Acme Synthetic"}),
        ("create_task_list", {}),
        ("create_ldc_entry", {}),
    ]

    outcomes = []
    for action, payload in actions:
        try:
            outcomes.append(
                workflow.execute_simulated_action(approval_id, 1, action, payload)[
                    "status"
                ]
            )
        except RuntimeError:
            outcomes.append("failed")
    retried = [
        workflow.execute_simulated_action(approval_id, 1, action, payload)["status"]
        for action, payload in actions
    ]

    assert outcomes == ["completed", "failed", "completed"]
    assert retried == ["already_completed", "completed", "already_completed"]
    # QC-REL-E-004 step 2: the same records as a run that had no failure
    assert _count(app_conn, "jobdiva_cases", approval_id) == 1
    assert _count(app_conn, "task_lists", approval_id) == 1
    assert _completed_audit(app_conn, case_id, "create_jobdiva_case") == 1
    assert _completed_audit(app_conn, case_id, "create_task_list") == 1
