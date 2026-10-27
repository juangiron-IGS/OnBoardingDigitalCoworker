"""Onboarding Knowledge agent (Should, US-025): answers onboarding process questions
from the knowledge base and cites the record (FR-KB-001). A record the Onboarding
Team has not validated is labelled as unvalidated (FR-KB-002); a rejected record is
never used; a question no record answers stays pending for the team (FR-KB-004). It
never answers FLSA, classification, compensation or legal questions (BR-001)."""

import re
from dataclasses import dataclass

from agents.common.model_client import RESTRICTED_TERMS
from contracts.mcp_tools import KnowledgeBase

AGENT = "onboarding_knowledge"

# Questions HR decides: never answered, never kept as text (restricted, BR-001).
HR_TOPICS = re.compile(
    RESTRICTED_TERMS
    + r"|\b(classif\w*|compensation|salary|pay rate|overtime|legal|lawsuit)\b",
    re.IGNORECASE,
)
HR_PLACEHOLDER = "FLSA, classification, compensation or legal question (text not kept)"
STOP = frozenset(
    "a an and are can do does for from get give has have how i in is it me my need "
    "needs new hire hires of on or should the their there this to what when where "
    "which who why will with you your".split()
)
MATCH_SHARE = 0.5  # more than half of the question's words must match a record


@dataclass(frozen=True)
class KnowledgeAnswer:
    reply: str
    status: str  # validated | unvalidated | no_answer | hr_decision
    record_id: str | None = None
    pending_id: str | None = None


def answer(
    question: str, kb: KnowledgeBase, *, asked_by: str, channel: str
) -> KnowledgeAnswer:
    text = question.strip()
    if not text:
        raise ValueError("question is empty")
    if HR_TOPICS.search(text):
        pending_id = kb.register_unresolved(
            HR_PLACEHOLDER, asked_by=asked_by, channel=channel, reason="hr_decision"
        )
        return KnowledgeAnswer(
            reply="I do not answer FLSA, classification, compensation or legal "
            "questions: HR decides them. I logged that you asked "
            f"({pending_id}) so the Onboarding Team can route it to HR.",
            status="hr_decision",
            pending_id=pending_id,
        )
    record = best_match(text, [r for r in kb.records() if r["status"] != "rejected"])
    if record is None:
        pending_id = kb.register_unresolved(
            text, asked_by=asked_by, channel=channel, reason="no_answer"
        )
        return KnowledgeAnswer(
            reply="I have no validated answer for that. I logged your question "
            f"({pending_id}) as pending for the Onboarding Team.",
            status="no_answer",
            pending_id=pending_id,
        )
    kb.log_answer(record["id"], record["status"], channel=channel)
    return KnowledgeAnswer(
        reply=compose(record), status=record["status"], record_id=record["id"]
    )


# US-031: the sections of the new-hire information package, in order.
PACKAGE_SECTIONS = [("company", "Company"), ("client", "Client"), ("role", "Role")]


def new_hire_package(data: dict, records: list[dict]) -> dict:
    """FR-NHP-001/002: company, client and role information from validated records
    only (BR-013), each citing its record; nothing restricted (BR-011)."""
    sections = []
    for category, heading in PACKAGE_SECTIONS:
        for record in records:
            if (
                record.get("audience") == "new_hire"
                and record["category"] == category
                and record["status"] == "validated"
                and _applies(record, data)
                and not HR_TOPICS.search(record["answer"])
            ):
                sections.append(
                    {
                        "heading": heading,
                        "title": record["title"],
                        "text": record["answer"],
                        "record_id": record["id"],
                    }
                )
    return {"person_ref": str(data.get("person_ref", "")), "sections": sections}


def _applies(record: dict, data: dict) -> bool:
    return all(
        str(data.get(field, "")).strip().casefold() == value.strip().casefold()
        for field, value in (record.get("applies_to") or {}).items()
    )


def best_match(question: str, records: list[dict]) -> dict | None:
    asked = _words(question)
    if not asked:
        return None

    def score(record: dict) -> tuple[int, bool]:
        known = _words(" ".join([record["question"], record["title"], *record["tags"]]))
        return len(asked & known), record["status"] == "validated"

    ranked = sorted(records, key=score, reverse=True)
    if ranked and score(ranked[0])[0] / len(asked) > MATCH_SHARE:
        return ranked[0]
    return None


def compose(record: dict) -> str:
    steps = "".join(f" {n}) {step}" for n, step in enumerate(record["steps"], start=1))
    body = record["answer"] + (f" Steps:{steps}" if steps else "")
    cite = f"Source: {record['id']} · {record['title']} ({record['source']})."
    if record["status"] == "validated":
        return f"{body} {cite} Validated by the Onboarding Team."
    return (
        f"Unvalidated draft, not yet confirmed by the Onboarding Team: {body} {cite} "
        "Check it with the Onboarding Team before relying on it."
    )


def _words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return {_stem(w) for w in words if w not in STOP and len(w) > 1}


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word
