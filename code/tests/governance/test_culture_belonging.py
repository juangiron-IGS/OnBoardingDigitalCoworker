"""Culture and Belonging (IGS): the LDC tracker handoff and the welcome kit after LDC
approval (US-028), and the leader messages LDC approves, with no restricted data
(US-029, BR-011)."""

from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.culture_belonging import agent as igs_agent
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
        igs=True,
    )


@pytest.fixture
def case_id(coworker) -> str:
    message = MAILBOX.read_message("01_complete_and_consistent")
    case_id = coworker.process_start(message["body"], source=message["from"]).case_id
    coworker.decide(
        case_id, package_version=1, decision="approve", approver_role="approver"
    )
    return case_id


def _rows(app_conn, store: str, case_id: str) -> list:
    return app_conn.execute(
        f"SELECT data FROM mocks.{store} WHERE case_id = %s",  # noqa: S608 - fixed names
        (case_id,),
    ).fetchall()


# --- US-028 ---


def test_approved_w2_hire_reaches_the_ldc_tracker(app_conn, case_id) -> None:
    # AC-001: accelerated timing and the assigned welcome kit
    entry = _rows(app_conn, "ldc_tracker", case_id)[0][0]

    assert entry["welcome_kit"] == "Employee welcome kit"
    assert entry["kit_ship_by"] < entry["start_date"] < entry["feedback_due"]
    assert entry["rule_id"] == "R-IG-01"


def test_kit_is_not_sent_without_ldc_approval(app_conn, coworker, case_id) -> None:
    # AC-002: asked to send the kit before LDC approves it, the writer refuses
    approval_id = coworker.cases.approval_id_for(case_id, 1)

    with pytest.raises(GovernanceError) as refusal:
        WorkflowService(app_conn).execute_simulated_action(
            approval_id, 1, "send_welcome_kit", {"welcome_kit": "Employee kit"}
        )
    assert refusal.value.reason == "kit_not_approved"
    assert _rows(app_conn, "welcome_kits", case_id) == []


def test_ldc_approval_ships_the_kit(app_conn, coworker, case_id) -> None:
    coworker.approve_welcome_kit(case_id, package_version=1, approved_by="ldc")

    shipment = _rows(app_conn, "welcome_kits", case_id)[0][0]
    assert shipment["welcome_kit"] == "Employee welcome kit"


def test_kit_approval_of_an_unapproved_case_is_refused(coworker) -> None:
    message = MAILBOX.read_message("01_complete_and_consistent")
    case_id = coworker.process_start(message["body"], source=message["from"]).case_id

    with pytest.raises(GovernanceError) as refusal:
        coworker.approve_welcome_kit(case_id, package_version=1, approved_by="ldc")
    assert refusal.value.reason == "case_not_approved"


# --- US-029 ---


def test_two_months_drafts_the_leader_messages(coworker, case_id) -> None:
    # AC-003
    early = coworker.run_igs_schedule(case_id, at_days=30)
    drafted = coworker.run_igs_schedule(case_id, at_days=60)

    messages = coworker.cases.leader_messages(case_id)
    assert early == []
    assert {d["kind"] for d in drafted} == {"feedback_request", "congratulation"}
    assert {m["status"] for m in messages} == {"draft"}
    assert messages[0]["recipient"] == "Pat Example"


def test_message_is_not_sent_before_ldc_approves_it(
    app_conn, coworker, case_id
) -> None:
    # AC-001
    coworker.run_igs_schedule(case_id, at_days=60)
    message = coworker.cases.leader_messages(case_id)[0]

    with pytest.raises(GovernanceError) as refusal:
        coworker.send_leader_message(case_id, message["id"])
    leader_alerts = app_conn.execute(
        "SELECT count(*) FROM mocks.alerts WHERE case_id = %s AND recipient = 'Leader'",
        (case_id,),
    ).fetchone()[0]
    assert refusal.value.reason == "message_not_approved"
    assert leader_alerts == 0


def test_approved_message_is_sent(app_conn, coworker, case_id) -> None:
    coworker.run_igs_schedule(case_id, at_days=60)
    message = coworker.cases.leader_messages(case_id)[0]

    coworker.approve_leader_message(case_id, message["id"], approved_by="ldc")

    sent = app_conn.execute(
        "SELECT text FROM mocks.alerts WHERE case_id = %s AND recipient = 'Leader'",
        (case_id,),
    ).fetchone()[0]
    assert sent == message["text"]
    assert coworker.cases.leader_messages(case_id)[0]["status"] == "sent"


def test_leader_messages_never_carry_restricted_data(coworker, case_id) -> None:
    # AC-002
    coworker.run_igs_schedule(case_id, at_days=60)

    text = " ".join(m["text"] for m in coworker.cases.leader_messages(case_id))
    assert "exempt" not in text.lower()
    assert "sponsor" not in text.lower()


def test_a_template_asking_for_flsa_is_refused() -> None:
    bad = Rule(
        id="R-IG-09",
        domain="igs",
        owner="LDC",
        version=1,
        status="draft",
        result={"kind": "congratulation", "template": "{person} is {flsa}"},
    )

    with pytest.raises(ValueError, match="may not use"):
        igs_agent.drafts({"person_ref": "SYN-1"}, RulesCatalog([bad]))


def test_a_draft_with_restricted_words_is_not_produced() -> None:
    leaky = Rule(
        id="R-IG-09",
        domain="igs",
        owner="LDC",
        version=1,
        status="draft",
        result={"kind": "congratulation", "template": "{role} ok"},
    )

    drafts = igs_agent.drafts({"role": "Exempt analyst"}, RulesCatalog([leaky]))

    assert drafts == []
