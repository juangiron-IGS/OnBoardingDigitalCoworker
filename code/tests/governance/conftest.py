import uuid
from datetime import date

import pytest

from services.case_service.adapters.postgres.audit_log import PostgresAuditLog
from services.case_service.adapters.postgres.case_repository import (
    PostgresCaseRepository,
)
from services.case_service.application.create_case import CaseIntake, create_case
from services.case_service.application.move_case import move_case
from services.case_service.domain.case import CaseState
from services.case_service.domain.package import PackageLine


class NoDuplicates:
    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        return {"found": False, "start_id": None}


@pytest.fixture
def repo(app_conn) -> PostgresCaseRepository:
    return PostgresCaseRepository(app_conn)


@pytest.fixture
def audit(app_conn) -> PostgresAuditLog:
    return PostgresAuditLog(app_conn)


@pytest.fixture
def case_set_up(repo, audit) -> str:
    """A case that passed validation and reached Case set up."""
    case_id = create_case(
        repo,
        audit,
        NoDuplicates(),
        CaseIntake(person_ref=f"person-{uuid.uuid4()}", start_date=date(2026, 11, 2)),
        agent="intake_validation",
    )
    move_case(repo, audit, case_id, CaseState.VALIDATED, agent="intake_validation")
    move_case(repo, audit, case_id, CaseState.CASE_SET_UP, agent="policy_case_setup")
    return case_id


@pytest.fixture
def lines() -> list[PackageLine]:
    return [
        PackageLine(
            field="work_state", value="CA", label="source", source_or_rule_id="jobdiva"
        ),
        PackageLine(
            field="paperwork",
            value="CA state forms",
            label="recommended",
            source_or_rule_id="R-PA-02",
        ),
    ]


@pytest.fixture
def approved_case(repo, audit, case_set_up, lines) -> tuple[str, str]:
    """A case whose package version 1 is approved: (case_id, approval_id)."""
    from services.case_service.application.build_package import build_package
    from services.case_service.application.decisions import record_approval

    build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    approval_id = record_approval(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )
    return case_set_up, approval_id
