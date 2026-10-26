import pytest

from services.case_service.application.build_package import build_package
from services.case_service.application.decisions import record_approval
from services.case_service.domain.errors import ApprovalRefused

pytestmark = pytest.mark.db


def test_approval_for_old_package_version_is_refused_and_audited(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # BR-002: an approval applies only to the current package version
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    with pytest.raises(ApprovalRefused) as refusal:
        record_approval(
            repo,
            audit,
            case_id=case_set_up,
            package_version=2,
            approver_role="approver",
        )

    outcome = app_conn.execute(
        "SELECT outcome FROM audit_log"
        " WHERE case_id = %s AND action = 'approve_package'",
        (case_set_up,),
    ).fetchone()[0]
    assert refusal.value.reason == "version_mismatch"
    assert outcome == "refused"
