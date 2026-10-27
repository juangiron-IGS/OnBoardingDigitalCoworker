"""US-031 (BR-011, BR-013): the new-hire information package holds company, client
and role information from validated knowledge only, is sent only after the
Onboarding Team reviews it, and never carries visa, sponsorship or FLSA data."""

from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.onboarding_knowledge.agent import new_hire_package
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.knowledge.service import KnowledgeService, load_records
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
        knowledge=KnowledgeService(app_conn),
    )


def _start(coworker, message_id: str, *, approve: bool) -> str:
    message = MAILBOX.read_message(message_id)
    case_id = coworker.process_start(message["body"], source=message["from"]).case_id
    if approve:
        coworker.decide(
            case_id, package_version=1, decision="approve", approver_role="approver"
        )
    return case_id


def test_package_holds_validated_company_client_and_role_information(
    coworker,
) -> None:
    # AC-001: Data Analyst at Acme Synthetic
    case_id = _start(coworker, "01_complete_and_consistent", approve=True)

    package = coworker.prepare_info_package(case_id)

    assert [s["record_id"] for s in package["content"]["sections"]] == [
        "KB-008",
        "KB-009",
        "KB-010",
    ]
    assert package["status"] == "draft"


def test_unvalidated_knowledge_never_enters_the_package() -> None:
    data = {"client": "Beta Synthetic Corp", "role": "Business Analyst"}
    rows = [r.model_dump(mode="json") for r in load_records()]

    sections = new_hire_package(data, rows)["sections"]

    assert [s["record_id"] for s in sections] == ["KB-008"]  # KB-011 is a draft


def test_package_is_sent_only_after_the_team_reviews_it(app_conn, coworker) -> None:
    case_id = _start(coworker, "01_complete_and_consistent", approve=True)

    with pytest.raises(GovernanceError) as not_prepared:
        coworker.send_info_package(case_id, reviewed_by="onboarding")
    coworker.prepare_info_package(case_id)
    candidate_before = app_conn.execute(
        "SELECT count(*) FROM mocks.alerts WHERE case_id = %s"
        " AND recipient = 'Candidate' AND text LIKE 'Your welcome information%%'",
        (case_id,),
    ).fetchone()[0]
    coworker.send_info_package(case_id, reviewed_by="onboarding")

    assert not_prepared.value.reason == "no_info_package"
    assert candidate_before == 0
    assert coworker.cases.info_package(case_id)["status"] == "sent"


def test_no_package_before_approval(coworker) -> None:
    case_id = _start(coworker, "01_complete_and_consistent", approve=False)

    with pytest.raises(GovernanceError) as refusal:
        coworker.prepare_info_package(case_id)
    assert refusal.value.reason == "case_not_approved"


def test_package_never_carries_restricted_data(coworker) -> None:
    # AC-002: the case has FLSA and sponsorship values
    case_id = _start(coworker, "01_complete_and_consistent", approve=True)

    package = coworker.prepare_info_package(case_id)

    text = " ".join(s["text"] for s in package["content"]["sections"]).lower()
    assert "exempt" not in text
    assert "sponsor" not in text
    assert "visa" not in text


def test_a_record_mentioning_a_visa_is_left_out() -> None:
    leaky = {
        "id": "KB-099",
        "audience": "new_hire",
        "category": "company",
        "status": "validated",
        "applies_to": {},
        "title": "Visa help",
        "answer": "We sponsor H-1B transfers.",
    }

    assert new_hire_package({}, [leaky])["sections"] == []
