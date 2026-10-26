import pytest

from services.case_service.application.build_package import build_package
from services.case_service.application.decisions import (
    authorize_action,
    record_approval,
    reject_case,
)
from services.case_service.domain.errors import GovernanceError

pytestmark = pytest.mark.db


def test_rejected_case_cannot_be_approved_or_acted_on(
    repo, audit, case_set_up, lines
) -> None:
    # US-013 AC-003: a rejected case stays stopped and no action runs
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    reject_case(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )

    with pytest.raises(GovernanceError):
        record_approval(
            repo,
            audit,
            case_id=case_set_up,
            package_version=1,
            approver_role="approver",
        )
    with pytest.raises(GovernanceError):
        build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    with pytest.raises(GovernanceError):
        authorize_action(repo, approval_id="apr-missing")
