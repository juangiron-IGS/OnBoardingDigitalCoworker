"""US-032: the supervisor is told of each new hire and assigns the follow-up owner.
US-010 AC-002: the Coworker only recommends; a person assigns."""

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

MAILBOX = Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"


class NoJobDivaDuplicates:
    def search_duplicate(self, person_ref, start_date) -> dict:
        return {"found": False, "start_id": None}


@pytest.fixture
def cases(app_conn) -> LocalCaseService:
    return LocalCaseService(app_conn, NoJobDivaDuplicates())


@pytest.fixture
def coworker(app_conn, cases) -> Orchestrator:
    return Orchestrator(
        cases=cases,
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
    )


@pytest.fixture
def set_up_case(coworker) -> str:
    message = MailboxService(MAILBOX).read_message("01_complete_and_consistent")
    return coworker.process_start(message["body"], source=message["from"]).case_id


def test_supervisor_is_notified_with_the_recommended_owner(app_conn, set_up_case):
    # AC-001
    text = app_conn.execute(
        "SELECT text FROM mocks.alerts WHERE case_id = %s AND recipient = %s",
        (set_up_case, "Onboarding Supervisor"),
    ).fetchone()[0]

    assert "Enterprise onboarding specialist" in text
    assert "R-OW-01" in text


def test_owner_is_recommended_until_a_person_assigns_it(cases, set_up_case):
    # US-010 AC-002
    view = cases.case_view(set_up_case, role="approver")

    assert view["case"]["recommended_owner"] == "Enterprise onboarding specialist"
    assert view["case"]["assigned_owner"] is None


def test_supervisor_assignment_is_shown_and_audited(app_conn, cases, set_up_case):
    # AC-002
    cases.assign_owner(
        set_up_case, "Enterprise onboarding specialist", assigned_by="approver"
    )

    view = cases.case_view(set_up_case, role="recruiter")
    agent, outcome, data_refs = app_conn.execute(
        "SELECT agent, outcome, data_refs FROM audit_log"
        " WHERE case_id = %s AND action = 'assign_owner'",
        (set_up_case,),
    ).fetchone()
    assert view["case"]["assigned_owner"] == "Enterprise onboarding specialist"
    assert (agent, outcome) == ("approver", "completed")
    assert data_refs == {"assigned_owner": "approver", "recommended_owner": "kept"}


def test_supervisor_assignment_replaces_recommendation_and_is_logged(
    app_conn, cases, set_up_case
):
    # AC-003
    cases.assign_owner(set_up_case, "Dana Synthetic", assigned_by="approver")

    view = cases.case_view(set_up_case, role="approver")
    data_refs = app_conn.execute(
        "SELECT data_refs FROM audit_log"
        " WHERE case_id = %s AND action = 'assign_owner'",
        (set_up_case,),
    ).fetchone()[0]
    assert view["case"]["assigned_owner"] == "Dana Synthetic"
    assert data_refs["recommended_owner"] == "replaced"


def test_owner_cannot_be_assigned_before_a_recommendation(app_conn, cases):
    message = MailboxService(MAILBOX).read_message("02_missing_two_fields")
    orchestrator = Orchestrator(
        cases=cases,
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
    )
    started = orchestrator.process_start(message["body"], source=message["from"])
    case_id = started.case_id

    with pytest.raises(GovernanceError) as refusal:
        cases.assign_owner(case_id, "Dana Synthetic", assigned_by="approver")
    assert refusal.value.reason == "no_recommendation"
