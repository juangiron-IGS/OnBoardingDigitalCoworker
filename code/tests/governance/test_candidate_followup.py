"""After approval: the candidate checklist and tiered reminders (US-022, BR-010), the
document check with the Onboarding Team's countersign (US-023) and the payroll
handoff and returns (US-024)."""

from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.jobdiva_workflow import agent as workflow_agent
from agents.orchestrator import orchestrator as orchestrator_module
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.outlook.service import MailboxService
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import Rule, RulesCatalog
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
        followup=True,
        payroll=True,
    )


@pytest.fixture
def case_id(coworker) -> str:
    message = MAILBOX.read_message("01_complete_and_consistent")
    case_id = coworker.process_start(message["body"], source=message["from"]).case_id
    coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )
    return case_id


def _items(coworker, case_id: str) -> dict[str, str]:
    return {c["item"]: c["status"] for c in coworker.cases.checklist(case_id)}


def _alerts(app_conn, case_id: str, recipient: str) -> list[str]:
    return [
        r[0]
        for r in app_conn.execute(
            "SELECT text FROM mocks.alerts WHERE case_id = %s AND recipient = %s"
            " ORDER BY id",
            (case_id, recipient),
        ).fetchall()
    ]


def _deliver_and_sign_all(coworker, case_id: str) -> None:
    items = list(_items(coworker, case_id))
    coworker.record_delivery(case_id, items, recorded_by="onboarding")
    for item in items:
        coworker.countersign(case_id, item, signed_by="onboarding")


# --- US-022 ---


def test_approved_case_sends_the_checklist(app_conn, coworker, case_id) -> None:
    # AC-001
    items = coworker.cases.checklist(case_id)

    assert coworker.cases.case_state(case_id).value == "documents_pending"
    assert {c["item"]: c["required_by"] for c in items}.items() >= {
        ("Federal withholding form (W-4)", "R-PA-01"),
        ("Emergency contact form", "R-CK-01"),
        ("Direct deposit form", "R-CK-02"),
    }
    assert all(c["status"] == "outstanding" for c in items)
    assert "W-4" in _alerts(app_conn, case_id, "Candidate")[0]


def test_checklist_never_names_an_flsa_status(app_conn, coworker, case_id) -> None:
    sent = _alerts(app_conn, case_id, "Candidate")[0]

    assert "exempt" not in sent.lower()
    assert "Employment agreement" in _items(coworker, case_id)


def test_reminders_at_24_and_48_hours_then_escalation(
    app_conn, coworker, case_id
) -> None:
    # AC-002
    at_24 = coworker.run_followup(case_id, at_hours=24)
    at_48 = coworker.run_followup(case_id, at_hours=48)
    at_60 = coworker.run_followup(case_id, at_hours=60)
    at_72 = coworker.run_followup(case_id, at_hours=72)
    at_96 = coworker.run_followup(case_id, at_hours=96)

    assert at_24 == [{"kind": "reminder", "at_hours": 24}]
    assert at_48 == [{"kind": "reminder", "at_hours": 48}]
    assert at_60 == []
    assert at_72 == [{"kind": "escalation", "at_hours": 72}]
    assert at_96 == []  # the send limit holds
    assert len(_alerts(app_conn, case_id, "Candidate")) == 3  # checklist + 2
    assert len(_alerts(app_conn, case_id, "Onboarding Team")) == 1


def test_no_reminder_once_everything_is_delivered(coworker, case_id) -> None:
    coworker.record_delivery(
        case_id, list(_items(coworker, case_id)), recorded_by="onboarding"
    )

    assert coworker.run_followup(case_id, at_hours=72) == []


def test_new_cadence_applies_to_the_next_reminders(
    coworker, case_id, monkeypatch
) -> None:
    # AC-003: the administrator changes the cadence rule
    rules = [r for r in RulesCatalog.load().all() if r.domain != "reminder"]
    faster = Rule(
        id="R-RM-01",
        domain="reminder",
        owner="Onboarding",
        version=2,
        status="draft",
        result={"every_hours": 12, "max_reminders": 1, "escalate_after_hours": 24},
    )
    monkeypatch.setattr(
        orchestrator_module.RulesCatalog, "load", lambda: RulesCatalog([*rules, faster])
    )

    sent = coworker.run_followup(case_id, at_hours=24)

    assert sent == [
        {"kind": "reminder", "at_hours": 12},
        {"kind": "escalation", "at_hours": 24},
    ]


# --- US-023 ---


def test_partial_delivery_lists_the_missing_items(coworker, case_id) -> None:
    # AC-001
    outcome = coworker.record_delivery(
        case_id, ["Emergency contact form"], recorded_by="onboarding"
    )

    assert "Direct deposit form" in outcome["missing"]
    assert "Emergency contact form" not in outcome["missing"]
    assert outcome["state"] == "documents_pending"


def test_delivered_document_is_not_verified_until_countersigned(
    coworker, case_id
) -> None:
    # AC-002
    coworker.record_delivery(
        case_id, ["Emergency contact form"], recorded_by="onboarding"
    )
    before = _items(coworker, case_id)["Emergency contact form"]
    coworker.countersign(case_id, "Emergency contact form", signed_by="onboarding")

    assert before == "pending_countersign"
    assert _items(coworker, case_id)["Emergency contact form"] == "verified"


def test_countersign_of_an_undelivered_document_is_refused_and_audited(
    app_conn, coworker, case_id
) -> None:
    with pytest.raises(GovernanceError) as refusal:
        coworker.countersign(case_id, "Direct deposit form", signed_by="onboarding")

    audited = app_conn.execute(
        "SELECT outcome FROM audit_log WHERE case_id = %s"
        " AND action = 'countersign_document'",
        (case_id,),
    ).fetchone()
    assert refusal.value.reason == "document_outstanding"
    assert audited == ("refused",)


def test_unknown_item_is_a_bad_request(coworker, case_id) -> None:
    with pytest.raises(ValueError, match="not on the checklist"):
        coworker.record_delivery(case_id, ["Passport photo"], recorded_by="onboarding")


def test_full_delivery_moves_to_verification(coworker, case_id) -> None:
    outcome = coworker.record_delivery(
        case_id, list(_items(coworker, case_id)), recorded_by="onboarding"
    )

    assert outcome == {"state": "in_verification", "missing": []}


# --- US-024 ---


def test_payroll_package_holds_validated_data_only() -> None:
    # AC-001
    lines = [
        {"field": "client", "value": "Acme Synthetic", "label": "source"},
        {"field": "owner", "value": "Specialist", "label": "recommended"},
        {"field": "work_city", "value": "Austin?", "label": "inferred"},
        {"field": "flsa", "value": "Conflict escalated", "label": "exception"},
        {"field": "bill_back", "value": "Client pays", "label": "recommended"},
    ]
    checklist = [
        {"item": "Emergency contact form", "status": "verified"},
        {"item": "Direct deposit form", "status": "pending_countersign"},
    ]

    payload = workflow_agent.payroll_package(lines, checklist)

    assert payload == {
        "client": "Acme Synthetic",
        "owner": "Specialist",
        "verified_documents": "Emergency contact form",
    }


def test_handoff_needs_every_document_verified(app_conn, coworker, case_id) -> None:
    items = list(_items(coworker, case_id))
    coworker.record_delivery(case_id, items, recorded_by="onboarding")

    with pytest.raises(GovernanceError) as refusal:
        coworker.approve_payroll_handoff(
            case_id, package_version=1, approved_by="onboarding"
        )
    sent = app_conn.execute(
        "SELECT count(*) FROM mocks.payroll_packages WHERE case_id = %s", (case_id,)
    ).fetchone()[0]
    assert refusal.value.reason == "documents_not_verified"
    assert sent == 0


def test_writer_refuses_the_package_without_handoff_approval(
    app_conn, coworker, case_id
) -> None:
    # AC-002: asked to send without the team's handoff approval, it does not
    _deliver_and_sign_all(coworker, case_id)
    approval_id = coworker.cases.approval_id_for(case_id, 1)

    with pytest.raises(GovernanceError) as refusal:
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 1, "send_payroll_package", {"client": "Acme Synthetic"}
        )
    assert refusal.value.reason == "handoff_not_approved"


def test_approved_handoff_sends_the_package(app_conn, coworker, case_id) -> None:
    _deliver_and_sign_all(coworker, case_id)

    outcome = coworker.approve_payroll_handoff(
        case_id, package_version=1, approved_by="onboarding"
    )

    data = app_conn.execute(
        "SELECT data FROM mocks.payroll_packages WHERE case_id = %s", (case_id,)
    ).fetchone()[0]
    assert outcome["state"] == "sent_to_payroll"
    assert data["client"] == "Acme Synthetic"
    assert "Emergency contact form" in data["verified_documents"]


def test_payroll_return_becomes_a_task_in_the_audit(
    app_conn, coworker, case_id
) -> None:
    # AC-003
    _deliver_and_sign_all(coworker, case_id)
    coworker.approve_payroll_handoff(
        case_id, package_version=1, approved_by="onboarding"
    )

    coworker.record_payroll_return(case_id, "Bank account does not match")

    audited = app_conn.execute(
        "SELECT agent FROM audit_log WHERE case_id = %s AND action = 'payroll_return'",
        (case_id,),
    ).fetchone()
    assert coworker.cases.payroll_returns(case_id)[0]["issue"] == (
        "Bank account does not match"
    )
    assert audited == ("payroll",)
    assert _alerts(app_conn, case_id, "Onboarding Team")


def test_payroll_record_hides_flsa_from_unauthorized_roles(coworker, case_id) -> None:
    _deliver_and_sign_all(coworker, case_id)
    coworker.approve_payroll_handoff(
        case_id, package_version=1, approved_by="onboarding"
    )

    it_view = coworker.cases.case_view(case_id, role="it")
    approver_view = coworker.cases.case_view(case_id, role="approver")

    def payroll(view):
        return next(r for r in view["records"] if r["system"] == "payroll_packages")

    assert payroll(it_view)["data"]["flsa"] == "Restricted"
    assert payroll(approver_view)["data"]["flsa"] != "Restricted"
