import pytest

from services.case_service.application.build_package import build_package
from services.case_service.application.decisions import (
    authorize_action,
    record_approval,
)
from services.case_service.domain.errors import ApprovalRefused

pytestmark = pytest.mark.db


def test_unknown_approval_id_is_refused(repo) -> None:
    # US-015 AC-001: no action without an approval
    with pytest.raises(ApprovalRefused) as refusal:
        authorize_action(repo, approval_id="apr-does-not-exist")
    assert refusal.value.reason == "no_approval"


def test_ready_package_without_decision_has_no_approval(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # US-036 AC-001: a case in Ready for review has not passed the gate
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    approvals = app_conn.execute(
        "SELECT count(*) FROM approvals WHERE case_id = %s", (case_set_up,)
    ).fetchone()[0]
    assert approvals == 0


def test_approval_authorizes_action_for_current_version(
    repo, audit, case_set_up, lines
) -> None:
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    approval_id = record_approval(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )

    approval = authorize_action(repo, approval_id=approval_id)

    assert (approval.case_id, approval.package_version) == (case_set_up, 1)


def test_action_refused_when_package_changed_after_approval(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # US-015 AC-003: version 1 was approved and version 2 now exists
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    approval_id = record_approval(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )
    app_conn.execute(
        "INSERT INTO package_versions (case_id, version, status)"
        " VALUES (%s, 2, 'ready')",
        (case_set_up,),
    )
    app_conn.execute(
        "UPDATE cases SET current_package_version = 2 WHERE id = %s", (case_set_up,)
    )

    with pytest.raises(ApprovalRefused) as refusal:
        authorize_action(repo, approval_id=approval_id)
    assert refusal.value.reason == "version_mismatch"
