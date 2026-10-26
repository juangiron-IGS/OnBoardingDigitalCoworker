import uuid
from datetime import date

import pytest

from contracts.case_service_api import CaseServiceClient
from services.case_service.application.create_case import CaseIntake
from services.case_service.domain.case import CaseState
from services.case_service.domain.package import PackageLine
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db


class NoDuplicates:
    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        return {"found": False, "start_id": None}


def test_local_service_fulfils_the_contract(app_conn) -> None:
    assert isinstance(LocalCaseService(app_conn, NoDuplicates()), CaseServiceClient)


def test_local_service_runs_intake_to_approval(app_conn) -> None:
    svc = LocalCaseService(app_conn, NoDuplicates())

    case_id = svc.create_case(
        CaseIntake(person_ref=f"person-{uuid.uuid4()}", start_date=date(2026, 11, 2)),
        agent="intake_validation",
    )
    svc.move_case(case_id, CaseState.VALIDATED, agent="intake_validation")
    svc.move_case(case_id, CaseState.CASE_SET_UP, agent="policy_case_setup")
    version = svc.build_package(
        case_id,
        [
            PackageLine(
                field="paperwork",
                value="CA state forms",
                label="recommended",
                source_or_rule_id="R-PA-02",
            )
        ],
        agent="orchestrator",
    )
    approval_id = svc.record_approval(
        case_id, package_version=version, approver_role="approver"
    )

    assert approval_id.startswith("apr-")
    assert svc.case_state(case_id) is CaseState.APPROVED
    assert svc.current_package_version(case_id) == 1
