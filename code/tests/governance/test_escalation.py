"""FLSA and classification conflicts are escalated, never decided (US-009, BR-001)."""

from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_read.adapters.mock import MockJobDiva
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


@pytest.fixture
def coworker(app_conn) -> Orchestrator:
    jobdiva = MockJobDiva()
    return Orchestrator(
        cases=LocalCaseService(app_conn, jobdiva),
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
        jobdiva=jobdiva,
    )


def _start(coworker, message_id: str):
    message = MAILBOX.read_message(message_id)
    return coworker.process_start(message["body"], source=message["from"])


def _lines(app_conn, case_id: str) -> dict[str, tuple[str, str, str]]:
    rows = app_conn.execute(
        "SELECT field, value, label, source_or_rule_id FROM package_lines"
        " WHERE case_id = %s",
        (case_id,),
    ).fetchall()
    return {field: (value, label, source) for field, value, label, source in rows}


def test_flsa_conflict_is_escalated_and_no_value_is_chosen(app_conn, coworker) -> None:
    # US-009 AC-001: email says Non-exempt, the JobDiva start notes say Exempt
    result = _start(coworker, "05_flsa_conflict")

    value, label, source = _lines(app_conn, result.case_id)["flsa"]
    status = app_conn.execute(
        "SELECT status FROM package_versions WHERE case_id = %s", (result.case_id,)
    ).fetchone()[0]
    assert label == "exception"
    assert "escalated" in value.lower()
    assert "Non-exempt" in value and "Exempt" in value
    assert source == "email vs JobDiva start notes"
    assert status == "blocked"


def test_escalation_alerts_onboarding_and_hr_without_values(app_conn, coworker) -> None:
    # BR-011: alerts name the field, never the FLSA values
    result = _start(coworker, "05_flsa_conflict")

    alerts = app_conn.execute(
        "SELECT recipient, text FROM mocks.alerts WHERE case_id = %s", (result.case_id,)
    ).fetchall()
    audit = app_conn.execute(
        "SELECT agent, data_refs FROM audit_log"
        " WHERE case_id = %s AND action = 'escalate_conflict'",
        (result.case_id,),
    ).fetchone()
    assert {recipient for recipient, _ in alerts} == {"Onboarding Team", "HR"}
    assert all("FLSA" in text for _, text in alerts)
    assert not any("exempt" in text.lower() for _, text in alerts)
    assert audit == ("policy_case_setup", {"flsa": "email vs JobDiva start notes"})


def test_escalated_package_cannot_be_approved(coworker) -> None:
    # US-009 AC-002: no HR answer, the case stays escalated and nothing runs
    result = _start(coworker, "05_flsa_conflict")

    with pytest.raises(GovernanceError) as refusal:
        coworker.decide(
            result.case_id,
            package_version=1,
            decision="approve",
            approver_role="approver",
        )
    assert refusal.value.reason == "package_not_ready"


def test_matching_values_are_not_escalated(app_conn, coworker) -> None:
    result = _start(coworker, "01_complete_and_consistent")

    _, label, source = _lines(app_conn, result.case_id)["flsa"]
    assert (label, source) == ("source", "email")


def test_duplicate_already_onboarding_in_jobdiva_is_blocked(coworker) -> None:
    # US-017 AC-001: the case exists in JobDiva, not in the case store
    reply = coworker.chat(
        "Candidate ID: SYN-0040\nStart date: 2026-11-02\nPosition: Analyst"
    )

    assert reply.state == "blocked_duplicate"
    assert "jobdiva:JD-START-1040" in reply.reply
