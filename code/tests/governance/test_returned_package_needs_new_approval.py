import pytest

from services.case_service.application.build_package import build_package
from services.case_service.application.decisions import (
    record_approval,
    return_package,
)
from services.case_service.application.move_case import move_case
from services.case_service.domain.case import CaseState
from services.case_service.domain.errors import ApprovalRefused

pytestmark = pytest.mark.db


def test_returned_package_goes_back_to_validated_and_old_approval_is_refused(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # US-013 AC-002, US-036 AC-002
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    return_package(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )
    state = app_conn.execute(
        "SELECT state FROM cases WHERE id = %s", (case_set_up,)
    ).fetchone()[0]
    assert state == CaseState.VALIDATED

    move_case(repo, audit, case_set_up, CaseState.CASE_SET_UP, agent="orchestrator")
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    with pytest.raises(ApprovalRefused) as refusal:
        record_approval(
            repo,
            audit,
            case_id=case_set_up,
            package_version=1,
            approver_role="approver",
        )
    assert refusal.value.reason == "version_mismatch"

    approval_id = record_approval(
        repo, audit, case_id=case_set_up, package_version=2, approver_role="approver"
    )
    assert approval_id.startswith("apr-")
