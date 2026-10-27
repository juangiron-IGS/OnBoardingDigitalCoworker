"""The chat channel of the Orchestrator: start a case (US-002), ask one question at a
time (US-003), answer status questions from the case record only (US-019) and route
process questions to the Onboarding Knowledge agent (US-025)."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.common.model_client import clean_value
from agents.onboarding_knowledge.agent import HR_TOPICS
from contracts.case_service_api import CaseState

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

CASE_REF = re.compile(r"\b(SYN-\d+|case-[0-9a-f]{12})\b", re.IGNORECASE)
QUESTION = re.compile(
    r"\?\s*$|^(how|what|which|where|when|who|why|can|do|does|is|are|should)\b",
    re.IGNORECASE,
)
ABOUT_CASE = re.compile(r"\b(status|doing|going|stuck)\b|\bthis case\b", re.IGNORECASE)

HELP = (
    "I can start an onboarding case or tell you how one is going. To start one, send "
    "the start details with at least the Candidate ID and the Start date (YYYY-MM-DD); "
    "'Label: value' lines always work. To ask about a case, include its candidate ID, "
    "for example: How is SYN-0043 doing? You can also ask an onboarding process "
    "question, for example: Which forms does a W-2 hire in Texas need?"
)

STATE_LABELS = {
    CaseState.RECEIVED: "Received",
    CaseState.BLOCKED_DUPLICATE: "Blocked: duplicate",
    CaseState.VALIDATED: "Validated",
    CaseState.NEEDS_CLARIFICATION: "Needs clarification",
    CaseState.CASE_SET_UP: "Case set up",
    CaseState.READY_FOR_REVIEW: "Ready for review",
    CaseState.APPROVAL_GATE: "Approval gate",
    CaseState.APPROVED: "Approved",
    CaseState.REJECTED: "Rejected",
    CaseState.ACTIONS_EXECUTED: "Actions executed",
    CaseState.DOCUMENTS_PENDING: "Documents pending",
    CaseState.IN_VERIFICATION: "In verification",
    CaseState.SENT_TO_PAYROLL: "Sent to payroll",
    CaseState.CLOSED: "Closed",
}


@dataclass(frozen=True)
class ChatReply:
    reply: str
    case_id: str | None = None
    state: str | None = None
    asking: str | None = None


def respond(
    orch: "Orchestrator",
    message: str,
    case_id: str | None,
    *,
    asked_by: str = "recruiter",
) -> ChatReply:
    text = message.strip()
    if not text:
        raise ValueError("message is empty")
    labelled = orch.read_labelled(text)

    open_fields = {q["field"] for q in orch.questions(case_id)} if case_id else set()
    # A question is never stored as an answer; labelled answers always count.
    answering = not QUESTION.search(text) or bool(open_fields & set(labelled))
    if open_fields and answering and not _is_new_start(labelled):
        return _continue(orch, case_id, text, labelled)
    if _is_new_start(labelled):
        return _start(orch, text)
    ref = CASE_REF.search(text)
    about_case = case_id and ABOUT_CASE.search(text)
    # FLSA, classification, visa or legal: HR decides; never sent to a model.
    if orch.knows and HR_TOPICS.search(text):
        answer = orch.ask_knowledge(text, asked_by=asked_by, channel="chat")
        return ChatReply(reply=answer.reply, case_id=case_id)
    # A process question with a knowledge record gets the record itself, cited.
    in_case = bool(case_id) and orch.model.provider != "rules"
    if orch.knows and QUESTION.search(text) and not (ref or about_case or in_case):
        answer = orch.ask_knowledge(
            text, asked_by=asked_by, channel="chat", register_unanswered=False
        )
        if answer.status != "no_answer":
            return ChatReply(reply=answer.reply, case_id=case_id)
    # Anything else Claude answers when the engine converses (assistant.py), in
    # the person's language, with read-only tools.
    from .assistant import converse

    reply = converse(orch, text, case_id=case_id, role=asked_by)
    if reply:
        return ChatReply(reply=reply, case_id=case_id)
    # Without a conversing engine: the fixed replies.
    if ref:
        return status(orch, ref.group(1))
    if about_case:
        return status(orch, case_id)
    if orch.knows and QUESTION.search(text):  # keep it pending (US-025)
        answer = orch.ask_knowledge(text, asked_by=asked_by, channel="chat")
        return ChatReply(reply=answer.reply, case_id=case_id)
    if case_id:
        return status(orch, case_id)
    return ChatReply(reply=HELP)


def status(orch: "Orchestrator", ref: str) -> ChatReply:
    """Answer only from the case record; never guess (FR-STS-002)."""
    case_id = orch.cases.find_case(_normalize(ref))
    if case_id is None:
        return ChatReply(reply=f"Information not available: I have no case for {ref}.")
    state = orch.cases.case_state(case_id)
    orch.cases.log_action(
        case_id,
        agent="orchestrator",
        action="answer_status",
        data_refs={"state": "case record"},
    )
    return ChatReply(
        reply=f"{orch.label(case_id)} is {STATE_LABELS.get(state, state.value)}: "
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
    if clean_value(next(iter(answers.values()))) is None:
        # "N/A", "-" or "pending" is not an answer: the field stays open.
        label = next(q["label"] for q in questions if q["field"] in answers)
        return ChatReply(
            reply=f'I still need the {label}: "{text}" is not a value. '
            f"What is the {label}?",
            case_id=case_id,
            state=orch.cases.case_state(case_id).value,
            asking=next(iter(answers)),
        )
    state = None
    for field_name, value in answers.items():
        state = orch.answer(case_id, field_name, value)
    return _next_step(orch, case_id, state, prefix="Thanks. ")


def _start(orch: "Orchestrator", text: str) -> ChatReply:
    result = orch.process_start(text, source="chat", channel="chat")
    if result.state == "needs_sender":
        return ChatReply(
            reply="I could not read the start date. Please send it as YYYY-MM-DD, "
            "for example Start date: 2026-11-23.",
            state=result.state,
        )
    if result.state == "blocked_duplicate":
        return ChatReply(
            reply="I did not create a new case: one already exists for this person "
            f"and start date ({result.label}).",
            state=result.state,
        )
    return _next_step(
        orch,
        result.case_id,
        result.state,
        prefix=f"I created the case for {result.label}. ",
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
    if state is CaseState.DOCUMENTS_PENDING:
        return "approved; waiting for the candidate to deliver the checklist documents"
    if state is CaseState.IN_VERIFICATION:
        return "documents delivered; the Onboarding Team verifies them"
    if state is CaseState.SENT_TO_PAYROLL:
        return "documents verified and the payroll package sent to Payroll (simulated)"
    if state is CaseState.APPROVED:
        return "approved, and the simulated actions are running"
    if state is CaseState.REJECTED:
        return "rejected by the approver, so it stays stopped"
    return "being set up by the Coworker"


def _is_new_start(labelled: dict[str, str]) -> bool:
    return bool(labelled.get("person_ref") and labelled.get("start_date"))


def _normalize(ref: str) -> str:
    return ref.upper() if ref.upper().startswith("SYN-") else ref.lower()
