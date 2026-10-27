"""Chat channel: start a case (US-002), adaptive questions one at a time (US-003)
and status questions answered from the record only (US-019)."""

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db

START = """Candidate ID: SYN-0050
Position: QA Engineer
Hiring manager: Lee Example
Start date: 2026-11-23
Client: Acme Synthetic
Client type: Enterprise
Division: Digital
Line of business: Professional Services
Employment type: W-2
Vendor company: INSPYR Solutions
Work arrangement: Hybrid
Pay rate: 40.00 USD/h
Work city: Los Angeles
Work state: CA
FLSA: Non-exempt
Billing contact: billing.acme@example.com
Equipment: Standard laptop, INSPYR
Sponsorship: No"""


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


def test_chat_starts_a_case_and_asks_one_question_at_a_time(coworker) -> None:
    first = coworker.chat(START)

    second = coworker.chat("61.00 USD/h", case_id=first.case_id)
    last = coworker.chat("Lee Example", case_id=first.case_id)

    assert first.case_id and first.state == "needs_clarification"
    assert first.asking == "bill_rate" and "Bill rate" in first.reply
    assert (
        second.asking == "timesheet_approver" and "Timesheet approver" in second.reply
    )
    assert last.state == "ready_for_review" and last.asking is None
    assert "package" in last.reply.lower()


def test_chat_package_lines_cite_the_chat(app_conn, coworker) -> None:
    started = coworker.chat(
        START + "\nBill rate: 61.00 USD/h\nTimesheet approver: Lee Example"
    )

    sources = {
        row[0]
        for row in app_conn.execute(
            "SELECT DISTINCT source_or_rule_id FROM package_lines"
            " WHERE case_id = %s AND label = 'source'",
            (started.case_id,),
        )
    }
    assert started.state == "ready_for_review"
    assert sources == {"chat"}


def test_status_question_names_state_and_who_acts(coworker) -> None:
    # US-019 AC-001
    coworker.chat(START + "\nBill rate: 61.00 USD/h\nTimesheet approver: Lee Example")

    answer = coworker.chat("How is SYN-0050 doing?")

    assert "Ready for review" in answer.reply
    assert "approver" in answer.reply.lower()


def test_status_of_a_case_waiting_names_the_open_fields(coworker) -> None:
    coworker.chat(START)

    answer = coworker.chat("status SYN-0050")

    assert "Needs clarification" in answer.reply
    assert "Bill rate" in answer.reply and "Timesheet approver" in answer.reply


def test_status_of_an_unknown_case_is_not_guessed(coworker) -> None:
    # US-019 AC-002
    answer = coworker.chat("How is SYN-9999 doing?")

    assert "not available" in answer.reply.lower()
    assert answer.case_id is None


def test_chat_without_start_data_says_what_is_needed(coworker) -> None:
    answer = coworker.chat("Hi, I have a new hire starting soon")

    assert answer.case_id is None
    assert "Candidate ID" in answer.reply and "Start date" in answer.reply


def test_duplicate_start_in_chat_is_blocked(coworker) -> None:
    first = coworker.chat(START)

    again = coworker.chat(START)

    assert again.state == "blocked_duplicate"
    assert "SYN-0050 · QA Engineer" in again.reply
    assert first.case_id not in again.reply  # people never see the internal ID


def test_empty_message_is_refused(coworker) -> None:
    with pytest.raises(ValueError, match="message"):
        coworker.chat("   ")


def test_a_placeholder_client_is_asked_of_the_recruiter(app_conn, coworker) -> None:
    # The client line says N/A: the case waits for it and the recruiter is alerted
    start = (
        START.replace("SYN-0050", "SYN-0051").replace(
            "Client: Acme Synthetic", "Client: N/A"
        )
        + "\nBill rate: 61.00 USD/h\nTimesheet approver: Lee Example"
    )

    reply = coworker.chat(start)
    alert = app_conn.execute(
        "SELECT text FROM mocks.alerts WHERE case_id = %s AND recipient = 'Recruiter'",
        (reply.case_id,),
    ).fetchone()[0]

    assert reply.state == "needs_clarification"
    assert reply.asking == "client"
    assert "Missing: Client" in alert


def test_a_placeholder_answer_keeps_the_question_open(coworker) -> None:
    start = (
        START.replace("SYN-0050", "SYN-0052").replace(
            "Client: Acme Synthetic", "Client: -"
        )
        + "\nBill rate: 61.00 USD/h\nTimesheet approver: Lee Example"
    )
    case_id = coworker.chat(start).case_id

    reply = coworker.chat("N/A", case_id=case_id)

    assert reply.asking == "client"
    assert "is not a value" in reply.reply
    assert "client" not in coworker.cases.case_data(case_id)


def test_status_lists_each_pending_item_with_its_team(coworker) -> None:
    # US-019 AC-001: what is pending and which team must act on it
    coworker.chat(START + "\nBill rate: 61.00 USD/h\nTimesheet approver: Lee Example")

    answer = coworker.chat("status SYN-0050")

    assert "Onboarding Team to review the onboarding path and paperwork" in (
        answer.reply
    )
    assert "Approver to decide on package v1" in answer.reply


def test_only_the_recruiter_answers_the_start_questions(coworker) -> None:
    # US-004: another role is told the recruiter must answer; nothing is stored
    case_id = coworker.chat(START).case_id

    reply = coworker.chat("61.00 USD/h", case_id=case_id, asked_by="ldc")

    assert "waiting for the recruiter to answer" in reply.reply
    assert "Bill rate" in reply.reply
    assert "bill_rate" not in coworker.cases.case_data(case_id)
