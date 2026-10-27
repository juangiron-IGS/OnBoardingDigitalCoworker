"""US-025 (BR-013): answers come from the knowledge base and cite the record; an
unvalidated record is labelled as such; a validated one is presented as confirmed;
a question no record answers stays pending for the Onboarding Team. FLSA and
classification questions are left to HR (BR-001)."""

import pytest

from agents.onboarding_knowledge import agent as knowledge
from mcp_servers.mocks.knowledge.service import KnowledgeService

pytestmark = pytest.mark.db


@pytest.fixture
def kb(app_conn) -> KnowledgeService:
    return KnowledgeService(app_conn)


def _ask(kb: KnowledgeService, question: str) -> knowledge.KnowledgeAnswer:
    return knowledge.answer(question, kb, asked_by="recruiter", channel="chat")


def _audit(app_conn, action: str) -> list[tuple]:
    return app_conn.execute(
        "SELECT agent, rule_ids, data_refs FROM audit_log"
        " WHERE case_id = 'knowledge' AND action = %s ORDER BY id",
        (action,),
    ).fetchall()


def test_answer_cites_the_matching_record(app_conn, kb) -> None:
    # AC-001
    answer = _ask(kb, "Which forms does a W-2 hire in Texas need?")

    assert answer.record_id == "KB-001"
    assert answer.status == "validated"
    assert "Source: KB-001" in answer.reply
    assert "Validated by the Onboarding Team" in answer.reply
    assert _audit(app_conn, "answer_from_knowledge")[-1][1] == ["KB-001"]


def test_unvalidated_record_is_labelled(kb) -> None:
    # AC-002
    answer = _ask(kb, "Which forms does a hire in Philadelphia need?")

    assert answer.record_id == "KB-005"
    assert answer.status == "unvalidated"
    assert answer.reply.startswith("Unvalidated draft")
    assert "Validated by the Onboarding Team" not in answer.reply


def test_validated_record_is_then_presented_as_confirmed(app_conn, kb) -> None:
    # AC-003
    kb.validate("KB-005", "validated", decided_by="onboarding")

    answer = _ask(kb, "Which forms does a hire in Philadelphia need?")

    assert answer.status == "validated"
    assert "Validated by the Onboarding Team" in answer.reply
    assert _audit(app_conn, "knowledge_validated")[-1][:2] == ("onboarding", ["KB-005"])


def test_rejected_record_is_never_used(kb) -> None:
    kb.validate("KB-006", "rejected", decided_by="onboarding")

    answer = _ask(kb, "What welcome kit does a corp-to-corp contractor get?")

    assert answer.record_id is None
    assert answer.status == "no_answer"


def test_unanswered_question_is_pending_for_the_team(kb) -> None:
    # AC-004
    answer = _ask(kb, "Which forms does a hire in Ohio need?")

    assert answer.status == "no_answer"
    assert "no validated answer" in answer.reply
    pending = kb.pending()[0]
    assert pending["id"] == answer.pending_id
    assert pending["question"] == "Which forms does a hire in Ohio need?"
    assert pending["reason"] == "no_answer"


def test_flsa_question_goes_to_hr_without_keeping_the_text(app_conn, kb) -> None:
    answer = _ask(kb, "Is SYN-0045 exempt or non-exempt?")

    assert answer.status == "hr_decision"
    assert answer.record_id is None
    pending = kb.pending()[0]
    assert pending["reason"] == "hr_decision"
    assert "exempt" not in pending["question"].replace("FLSA", "")
    assert "SYN-0045" not in pending["question"]


def test_unknown_record_cannot_be_validated(kb) -> None:
    with pytest.raises(KeyError):
        kb.validate("KB-999", "validated", decided_by="onboarding")


@pytest.mark.parametrize(
    "question",
    ["Does an H-1B transfer need a new I-9?", "Can a hire on OPT start early?"],
)
def test_visa_question_is_not_kept_as_text(kb, question) -> None:
    answer = _ask(kb, question)

    assert answer.status == "hr_decision"
    assert kb.pending()[0]["question"] == knowledge.HR_PLACEHOLDER
