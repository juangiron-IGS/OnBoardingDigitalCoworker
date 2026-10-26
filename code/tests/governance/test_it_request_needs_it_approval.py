"""US-020 AC-002 (BR-012): the laptop request reaches the simulated Chelsea Tech only
after both the approver and IT approve the current package version."""

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


def _coworker(app_conn, *, access_equipment: bool) -> Orchestrator:
    return Orchestrator(
        cases=LocalCaseService(app_conn, NoJobDivaDuplicates()),
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
        access_equipment=access_equipment,
    )


@pytest.fixture
def coworker(app_conn) -> Orchestrator:
    return _coworker(app_conn, access_equipment=True)


@pytest.fixture
def case_id(coworker) -> str:
    message = MailboxService(MAILBOX).read_message("01_complete_and_consistent")
    return coworker.process_start(message["body"], source=message["from"]).case_id


def _it_requests(app_conn, case_id: str) -> int:
    return app_conn.execute(
        "SELECT count(*) FROM mocks.it_requests WHERE case_id = %s", (case_id,)
    ).fetchone()[0]


def test_request_waits_for_it_after_the_approver_approves(
    app_conn, coworker, case_id
) -> None:
    outcome = coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )

    it_alert = app_conn.execute(
        "SELECT count(*) FROM mocks.alerts WHERE case_id = %s AND recipient = 'IT'",
        (case_id,),
    ).fetchone()[0]
    assert outcome["state"] == "actions_executed"
    assert _it_requests(app_conn, case_id) == 0
    assert it_alert == 1


def test_request_is_sent_once_both_have_approved(app_conn, coworker, case_id) -> None:
    coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )

    coworker.approve_it_request(case_id, package_version=1, approver_role="it")

    row = app_conn.execute(
        "SELECT data FROM mocks.it_requests WHERE case_id = %s", (case_id,)
    ).fetchone()[0]
    assert row["provider"] == "Chelsea Tech"


def test_it_first_then_approver_sends_the_request(app_conn, coworker, case_id) -> None:
    coworker.approve_it_request(case_id, package_version=1, approver_role="it")

    coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )

    assert _it_requests(app_conn, case_id) == 1


def test_writer_refuses_the_request_without_it_approval(
    app_conn, coworker, case_id
) -> None:
    approval_id = coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )["approval_id"]

    with pytest.raises(GovernanceError) as refusal:
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 1, "create_it_request", {"provider": "Chelsea Tech"}
        )

    refused = app_conn.execute(
        "SELECT count(*) FROM audit_log WHERE case_id = %s"
        " AND action = 'create_it_request' AND outcome = 'refused'",
        (case_id,),
    ).fetchone()[0]
    assert refusal.value.reason == "it_not_approved"
    assert refused == 1


def test_it_approval_of_an_old_version_is_refused(coworker, case_id) -> None:
    with pytest.raises(GovernanceError) as refusal:
        coworker.approve_it_request(case_id, package_version=2, approver_role="it")
    assert refusal.value.reason == "version_mismatch"


def test_feature_off_adds_no_equipment_lines(app_conn) -> None:
    coworker = _coworker(app_conn, access_equipment=False)
    message = MailboxService(MAILBOX).read_message("01_complete_and_consistent")
    case_id = coworker.process_start(message["body"], source=message["from"]).case_id

    fields = {
        row[0]
        for row in app_conn.execute(
            "SELECT field FROM package_lines WHERE case_id = %s", (case_id,)
        ).fetchall()
    }
    assert "equipment_request" not in fields
