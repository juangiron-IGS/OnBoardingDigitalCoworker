"""The chat channel of the Orchestrator: start a case (US-002), ask one question at a
time (US-003) and answer status questions from the case record only (US-019)."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from contracts.case_service_api import CaseState

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

CASE_REF = re.compile(r"\b(SYN-\d+|case-[0-9a-f]{12})\b", re.IGNORECASE)

HELP = (
    "I can start an onboarding case or tell you how one is going. To start one, send "
    "the start details as 'Label: value' lines, at least Candidate ID and Start date "
    "(YYYY-MM-DD). To ask about a case, include its candidate ID, for example: "
    "How is SYN-0043 doing?"
)

STATE_LABELS = {
    CaseState.RECEIVED: "Received",
    CaseState.VALIDATED: "Validated",
    CaseState.NEEDS_CLARIFICATION: "Needs clarification",
    CaseState.CASE_SET_UP: "Case set up",
    CaseState.READY_FOR_REVIEW: "Ready for review",
    CaseState.APPROVAL_GATE: "Approval gate",
    CaseState.APPROVED: "Approved",
    CaseState.REJECTED: "Rejected",
    CaseState.ACTIONS_EXECUTED: "Actions executed",
    CaseState.CLOSED: "Closed",
}


@dataclass(frozen=True)
class ChatReply:
    reply: str
    case_id: str | None = None
    state: str | None = None
    asking: str | None = None


def respond(orch: "Orchestrator", message: str, case_id: str | None) -> ChatReply:
    text = message.strip()
    if not text:
        raise ValueError("message is empty")
    labelled = orch.read_labelled(text)

    if case_id and orch.questions(case_id) and not _is_new_start(labelled):
        return _continue(orch, case_id, text, labelled)
    if _is_new_start(labelled):
        return _start(orch, text)
    ref = CASE_REF.search(text)
    if ref:
        return status(orch, ref.group(1))
    if case_id:
        return status(orch, case_id)
    return ChatReply(reply=HELP)


def status(orch: "Orchestrator", ref: str) -> ChatReply:
    """Answer only from the case record; never guess (FR-STS-002)."""
    case_id = orch.cases.find_case(_normalize(ref))
    if case_id is None:
        return ChatReply(reply=f"Information not available: I have no case for {ref}.")
    state = orch.cases.case_state(case_id)
    person = orch.cases.case_data(case_id).get("person_ref", case_id)
    orch.cases.log_action(
        case_id,
        agent="orchestrator",
        action="answer_status",
        data_refs={"state": "case record"},
    )
    return ChatReply(
        reply=f"{person} ({case_id}) is {STATE_LABELS.get(state, state.value)}: "
        f"{_who_acts(orch, case_id, state)}.",
        case_id=case_id,
        state=state.value,
    )


def _continue(
    orch: "Orchestrator", case_id: str, text: str, labelled: dict[str, str]
) -> ChatReply:
    questions = orch.questions(case_id)
    open_fields = {q["field"] for q in questions}
    answers = {f: v for f, v in labelled.items() if f in open_fields}
    if not answers:
        # A plain reply answers the question that was asked: the first open one.
        answers = {questions[0]["field"]: text}
    state = None
    for field_name, value in answers.items():
        state = orch.answer(case_id, field_name, value)
    return _next_step(orch, case_id, state, prefix="Thanks. ")


def _start(orch: "Orchestrator", text: str) -> ChatReply:
    result = orch.process_start(text, source="chat", channel="chat")
    if result.state == "blocked_duplicate":
        return ChatReply(
            reply="I did not create a new case: one already exists for this person "
            f"and start date ({result.blocked_by}).",
            state=result.state,
        )
    return _next_step(
        orch, result.case_id, result.state, prefix=f"I created case {result.case_id}. "
    )


def _next_step(
    orch: "Orchestrator", case_id: str, state: str | None, *, prefix: str
) -> ChatReply:
    questions = orch.questions(case_id)
    if state == CaseState.NEEDS_CLARIFICATION.value and questions:
        question = questions[0]
        ask = (
            f"What is the {question['label']}?"
            if question["kind"] == "missing"
            else f"Two different values were given for {question['label']}. "
            "Which one is right?"
        )
        remaining = len(questions) - 1
        more = f" ({remaining} more after this)" if remaining else ""
        return ChatReply(
            reply=prefix + ask + more,
            case_id=case_id,
            state=state,
            asking=question["field"],
        )
    version = orch.cases.current_package_version(case_id)
    return ChatReply(
        reply=prefix
        + f"The case is complete and package v{version} is ready for the approver.",
        case_id=case_id,
        state=state,
    )


def _who_acts(orch: "Orchestrator", case_id: str, state: CaseState) -> str:
    if state is CaseState.NEEDS_CLARIFICATION:
        labels = " and ".join(q["label"] for q in orch.questions(case_id))
        return f"waiting for the recruiter to answer {labels}"
    if state in (CaseState.READY_FOR_REVIEW, CaseState.APPROVAL_GATE):
        version = orch.cases.current_package_version(case_id)
        return (
            "waiting for the approver (Consultant Onboarding Supervisor) to decide on "
            f"package v{version}"
        )
    if state is CaseState.ACTIONS_EXECUTED:
        return "approved, and the simulated JobDiva case and task list were created"
    if state is CaseState.APPROVED:
        return "approved, and the simulated actions are running"
    if state is CaseState.REJECTED:
        return "rejected by the approver, so it stays stopped"
    return "being set up by the Coworker"


def _is_new_start(labelled: dict[str, str]) -> bool:
    return bool(labelled.get("person_ref") and labelled.get("start_date"))


def _normalize(ref: str) -> str:
    return ref.upper() if ref.upper().startswith("SYN-") else ref.lower()
