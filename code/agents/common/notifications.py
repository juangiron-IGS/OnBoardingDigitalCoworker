"""Shared notifications tool (not an agent): wording per audience, sent through the
Teams mock. Messages name fields, never restricted values (BR-011)."""

from contracts.mcp_tools import Alerts


def label(field: str, labels: dict[str, list[str]]) -> str:
    return labels.get(field, [field])[0]


def missing_fields_text(
    case_id: str,
    missing: list[str],
    contradictions: list[str],
    labels: dict[str, list[str]],
) -> str:
    parts = []
    if missing:
        names = ", ".join(label(f, labels) for f in missing)
        parts.append(f"Missing: {names}.")
    if contradictions:
        names = ", ".join(label(f, labels) for f in contradictions)
        parts.append(
            f"Two different values were given for: {names}. Please confirm one."
        )
    return f"Case {case_id} needs your answer. " + " ".join(parts)


def duplicate_text(existing_ref: str) -> str:
    return (
        "This start was not processed: a case for the same person and start date "
        f"already exists ({existing_ref})."
    )


def notify(alerts: Alerts, case_id: str, recipient: str, text: str) -> None:
    alerts.post_alert(case_id, recipient, text)
