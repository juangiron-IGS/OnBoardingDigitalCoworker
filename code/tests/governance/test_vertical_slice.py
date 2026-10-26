"""J1 and J2 end to end on the seed emails, in-process (one rolled-back connection)."""

from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.outlook.service import MailboxService
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db

MAILBOX = Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"


class NoJobDivaDuplicates:
    def search_duplicate(self, person_ref, start_date) -> dict:
        return {"found": False, "start_id": None}


@pytest.fixture
def mailbox() -> MailboxService:
    return MailboxService(MAILBOX)


@pytest.fixture
def coworker(app_conn) -> Orchestrator:
    return Orchestrator(
        cases=LocalCaseService(app_conn, NoJobDivaDuplicates()),
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
    )


def _start(coworker, mailbox, message_id: str):
    message = mailbox.read_message(message_id)
    return coworker.process_start(message["body"], source=message["from"])


def test_complete_email_produces_a_ready_package_with_rule_ids(
    app_conn, coworker, mailbox
) -> None:
    # J1: US-001 AC-001, US-007 AC-002, US-011 AC-001/002
    result = _start(coworker, mailbox, "01_complete_and_consistent")

    lines = app_conn.execute(
        "SELECT field, value, label, source_or_rule_id FROM package_lines"
        " WHERE case_id = %s ORDER BY id",
        (result.case_id,),
    ).fetchall()
    assert result.state == "ready_for_review"
    assert (
        "paperwork",
        "CA state withholding form (DE 4)",
        "recommended",
        "R-PA-02",
    ) in lines
    assert all(
        label in {"source", "inferred", "recommended", "exception"}
        for _, _, label, _ in lines
    )
    assert all(source for *_, source in lines)


def test_missing_fields_alert_names_exact_fields_and_is_audited(
    app_conn, coworker, mailbox
) -> None:
    # US-004 AC-002, US-006 AC-001/002
    result = _start(coworker, mailbox, "02_missing_two_fields")

    alert = app_conn.execute(
        "SELECT recipient, text FROM mocks.alerts WHERE case_id = %s", (result.case_id,)
    ).fetchone()
    audit = app_conn.execute(
        "SELECT data_refs FROM audit_log"
        " WHERE case_id = %s AND action = 'alert_recruiter'",
        (result.case_id,),
    ).fetchone()[0]
    assert result.state == "needs_clarification"
    assert result.missing == ["bill_rate", "timesheet_approver"]
    assert "Timesheet approver" in alert[1] and "Bill rate" in alert[1]
    assert "data incomplete" not in alert[1].lower()
    assert set(audit) == {"bill_rate", "timesheet_approver"}


def test_answers_complete_the_case_and_build_the_package(coworker, mailbox) -> None:
    # Checkpoint demo: the recruiter answers the 2 fields, the package follows
    result = _start(coworker, mailbox, "02_missing_two_fields")

    coworker.answer(result.case_id, "timesheet_approver", "Lee Example")
    state = coworker.answer(result.case_id, "bill_rate", "61.00 USD/h")

    assert state == "ready_for_review"


def test_unknown_answer_field_is_refused(coworker, mailbox) -> None:
    result = _start(coworker, mailbox, "02_missing_two_fields")

    with pytest.raises(ValueError, match="field"):
        coworker.answer(result.case_id, "salary_secret", "1")


def test_duplicate_email_is_blocked_and_names_the_case(
    app_conn, coworker, mailbox
) -> None:
    # US-017
    first = _start(coworker, mailbox, "01_complete_and_consistent")

    second = _start(coworker, mailbox, "03_duplicate")

    alert = app_conn.execute(
        "SELECT text FROM mocks.alerts WHERE case_id = %s", (first.case_id,)
    ).fetchone()[0]
    assert second.state == "blocked_duplicate"
    assert second.case_id is None and second.blocked_by == first.case_id
    assert first.case_id in alert


def test_contradiction_asks_for_one_work_arrangement(coworker, mailbox) -> None:
    # US-003 AC-002, US-005 AC-002
    result = _start(coworker, mailbox, "04_work_arrangement_contradiction")

    assert result.state == "needs_clarification"
    assert result.contradictions == ["work_arrangement"]


def test_approval_runs_the_actions_through_the_single_writer(
    app_conn, coworker, mailbox
) -> None:
    # J2: US-013, US-015 AC-002, US-034 AC-003; AC8 three agents on one case
    result = _start(coworker, mailbox, "01_complete_and_consistent")

    outcome = coworker.decide(
        result.case_id, package_version=1, decision="approve", approver_role="approver"
    )

    records = app_conn.execute(
        "SELECT (SELECT count(*) FROM mocks.jobdiva_cases WHERE approval_id = %(a)s),"
        " (SELECT count(*) FROM mocks.task_lists WHERE approval_id = %(a)s)",
        {"a": outcome["approval_id"]},
    ).fetchone()
    agents = {
        row[0]
        for row in app_conn.execute(
            "SELECT DISTINCT agent FROM audit_log WHERE case_id = %s", (result.case_id,)
        )
    }
    assert outcome["state"] == "actions_executed"
    assert records == (1, 1)
    assert {"intake_validation", "policy_case_setup", "jobdiva_workflow"} <= agents


def test_returned_package_goes_back_for_correction(coworker, mailbox) -> None:
    result = _start(coworker, mailbox, "01_complete_and_consistent")

    outcome = coworker.decide(
        result.case_id, package_version=1, decision="return", approver_role="approver"
    )

    assert outcome["state"] == "validated"
    assert outcome["approval_id"] is None
