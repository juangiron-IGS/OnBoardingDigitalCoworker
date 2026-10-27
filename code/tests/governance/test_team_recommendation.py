"""US-026 (BR-006): the Onboarding Team confirms or changes the recommended path
and paperwork. A change replaces the recommendation and makes a new package
version; earlier versions are kept and their approvals no longer apply."""

from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.outlook.service import MailboxService
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.errors import GovernanceError
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db

MAILBOX = MailboxService(
    Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"
)


class NoJobDivaDuplicates:
    def search_duplicate(self, person_ref, start_date) -> dict:
        return {"found": False, "start_id": None}


@pytest.fixture
def coworker(app_conn) -> Orchestrator:
    return Orchestrator(
        cases=LocalCaseService(app_conn, NoJobDivaDuplicates()),
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
    )


@pytest.fixture
def case_id(coworker) -> str:
    message = MAILBOX.read_message("01_complete_and_consistent")
    return coworker.process_start(message["body"], source=message["from"]).case_id


def _lines(app_conn, case_id: str, version: int, field: str) -> list[tuple]:
    return app_conn.execute(
        "SELECT value, label, source_or_rule_id FROM package_lines"
        " WHERE case_id = %s AND version = %s AND field = %s ORDER BY id",
        (case_id, version, field),
    ).fetchall()


def test_team_confirms_the_recommendation(app_conn, coworker, case_id) -> None:
    # AC-001: recorded on the case and in the audit; the package content is unchanged
    outcome = coworker.review_recommendation(
        case_id, "paperwork", confirm=True, reviewed_by="onboarding"
    )

    data = coworker.cases.case_data(case_id)
    audit = app_conn.execute(
        "SELECT agent, data_refs FROM audit_log"
        " WHERE case_id = %s AND action = 'confirm_recommendation'",
        (case_id,),
    ).fetchone()
    assert outcome == {"state": "ready_for_review", "package_version": 1}
    assert data["team_review"]["paperwork"] == {"confirmed": True, "version": 1}
    assert audit == ("onboarding", {"paperwork": "Onboarding Team"})


def test_team_change_makes_a_new_version(app_conn, coworker, case_id) -> None:
    # AC-002: the change replaces the recommendation in a new version
    outcome = coworker.review_recommendation(
        case_id,
        "paperwork",
        values=["Federal withholding form (W-4)", "Client NDA"],
        reviewed_by="onboarding",
    )

    assert outcome == {"state": "ready_for_review", "package_version": 2}
    assert _lines(app_conn, case_id, 2, "paperwork") == [
        ("Federal withholding form (W-4)", "source", "Onboarding Team"),
        ("Client NDA", "source", "Onboarding Team"),
    ]
    assert _lines(app_conn, case_id, 1, "paperwork")  # v1 is kept
    assert _lines(app_conn, case_id, 2, "path")[0][1] == "recommended"


def test_approval_of_the_old_version_is_refused_after_a_change(
    coworker, case_id
) -> None:
    coworker.review_recommendation(
        case_id, "path", values=["Contractor onboarding"], reviewed_by="onboarding"
    )

    with pytest.raises(GovernanceError) as refusal:
        coworker.decide(
            case_id, package_version=1, decision="approve", approver_role="approver"
        )
    assert refusal.value.reason == "version_mismatch"


def test_only_path_and_paperwork_can_be_reviewed(coworker, case_id) -> None:
    with pytest.raises(ValueError, match="path or paperwork"):
        coworker.review_recommendation(
            case_id, "flsa", values=["Exempt"], reviewed_by="onboarding"
        )


def test_no_review_after_approval(coworker, case_id) -> None:
    coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )

    with pytest.raises(GovernanceError):
        coworker.review_recommendation(
            case_id, "path", values=["Contractor onboarding"], reviewed_by="onboarding"
        )
