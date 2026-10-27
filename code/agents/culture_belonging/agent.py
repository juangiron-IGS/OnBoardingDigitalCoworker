"""Culture and Belonging agent (Could, US-028, US-029): hands an approved W-2 hire
to the LDC tracker with accelerated timing and the assigned welcome kit, and drafts
the leader feedback request and congratulation at two months. Nothing is sent before
LDC approves it, and no message carries FLSA, visa or sponsorship data (BR-011)."""

import re
import string
from datetime import date, timedelta

from agents.common.model_client import RESTRICTED_TERMS
from services.case_service.adapters.rules_files.catalog import RulesCatalog

AGENT = "culture_belonging"
# The only case values a leader message may use.
MESSAGE_FIELDS = {"person": "person_ref", "role": "role", "client": "client"}
_RESTRICTED = re.compile(RESTRICTED_TERMS, re.IGNORECASE)


def plan(data: dict, lines: list[dict], catalog: RulesCatalog) -> dict | None:
    """The LDC tracker entry for this hire, or None when the case needs no IGS."""
    timing = [
        r for r in catalog.matching("igs", data) if "feedback_after_days" in r.result
    ]
    if not timing:
        return None
    rule = timing[0]
    start = date.fromisoformat(str(data["start_date"]))
    kit = next(
        (
            line["value"]
            for line in lines
            if line["field"] == "welcome_kit" and line["label"] != "exception"
        ),
        None,
    )
    return {
        "rule_id": rule.id,
        "person_ref": str(data["person_ref"]),
        "role": str(data.get("role", "")),
        "client": str(data.get("client", "")),
        "start_date": start.isoformat(),
        "welcome_kit": kit or "To be assigned by LDC",
        "kit_ship_by": (
            start - timedelta(days=int(rule.result["kit_ship_days_before_start"]))
        ).isoformat(),
        "feedback_due": (
            start + timedelta(days=int(rule.result["feedback_after_days"]))
        ).isoformat(),
    }


def drafts(data: dict, catalog: RulesCatalog) -> list[tuple[str, str, str]]:
    """(kind, text, rule ID) of the leader messages, from the LDC templates. A
    template may only use person, role, client and start; a draft that would carry
    restricted data is not produced (US-029 AC-002)."""
    values = {key: str(data.get(field, "")) for key, field in MESSAGE_FIELDS.items()}
    values["start"] = str(data.get("start_date", ""))
    result = []
    for rule in catalog.matching("igs", data):
        template = rule.result.get("template")
        if not template:
            continue
        fields = {f for _, f, _, _ in string.Formatter().parse(str(template)) if f}
        if not fields <= set(values):
            raise ValueError(f"{rule.id} uses a field a leader message may not use")
        text = str(template).format(**values)
        if _RESTRICTED.search(text):
            continue
        result.append((str(rule.result["kind"]), text, rule.id))
    return result
