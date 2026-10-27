"""Candidate Follow-up agent (Should, US-022, US-023): builds the candidate checklist
from the approved package and the checklist rules, and decides which reminders or
escalation are due under the cadence rule (BR-010). It never verifies a document:
the Onboarding Team countersigns (FR-DOC-002)."""

import re
from dataclasses import dataclass

from agents.common.model_client import RESTRICTED_TERMS
from services.case_service.adapters.rules_files.catalog import RulesCatalog

AGENT = "candidate_followup"
# A form named after an FLSA status would reveal it in messages (BR-011).
_RESTRICTED = re.compile(RESTRICTED_TERMS, re.IGNORECASE)
NEUTRAL_FORM = "Employment agreement"


@dataclass(frozen=True)
class Cadence:
    rule_id: str
    every_hours: int
    max_reminders: int
    escalate_after_hours: int


def checklist(
    lines: list[dict], data: dict, catalog: RulesCatalog
) -> list[tuple[str, str]]:
    """(item, required by): the paperwork of the approved package plus the items
    every candidate delivers. Exception lines are never sent to a candidate."""
    items = [
        (_neutral(line["value"]), line["source_or_rule_id"])
        for line in lines
        if line["field"] == "paperwork" and line["label"] != "exception"
    ]
    items += [
        (str(r.result["item"]), r.id) for r in catalog.matching("checklist", data)
    ]
    unique: dict[str, str] = {}
    for item, required_by in items:
        unique.setdefault(item, required_by)
    return list(unique.items())


def _neutral(form: str) -> str:
    return NEUTRAL_FORM if _RESTRICTED.search(form) else form


def cadence(catalog: RulesCatalog) -> Cadence:
    rule = catalog.rules("reminder")[0]
    return Cadence(
        rule_id=rule.id,
        every_hours=int(rule.result["every_hours"]),
        max_reminders=int(rule.result["max_reminders"]),
        escalate_after_hours=int(rule.result["escalate_after_hours"]),
    )


def due(
    outstanding: int, sent: list[dict], rule: Cadence, at_hours: int
) -> list[tuple[str, int]]:
    """(kind, at hour) of the reminders and escalation due by `at_hours`, given
    what was already sent. Nothing is due once every item is delivered."""
    if not outstanding:
        return []
    reminders = sum(1 for s in sent if s["kind"] == "reminder")
    escalated = any(s["kind"] == "escalation" for s in sent)
    result = [
        ("reminder", n * rule.every_hours)
        for n in range(reminders + 1, rule.max_reminders + 1)
        if n * rule.every_hours <= at_hours
    ]
    if not escalated and at_hours >= rule.escalate_after_hours:
        result.append(("escalation", rule.escalate_after_hours))
    return result
