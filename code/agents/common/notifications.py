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


def escalation_text(
    case_id: str, fields: list[str], labels: dict[str, list[str]]
) -> str:
    names = ", ".join(label(f, labels) for f in fields)
    return (
        f"Case {case_id}: {names} differs between the start email and the JobDiva "
        "start notes. It is escalated for your decision; the Coworker has not chosen "
        "a value."
    )


def owner_text(case_id: str, owner: str, rule_id: str) -> str:
    return (
        f"New hire in case {case_id}. Recommended follow-up owner: {owner} "
        f"({rule_id}). Please assign the owner in the approval view."
    )


def it_request_text(case_id: str, package_version: int) -> str:
    return (
        f"Case {case_id}: package v{package_version} is approved. The laptop and "
        "access request waits for your approval in the approval view."
    )


def checklist_text(case_id: str, items: list[str]) -> str:
    return (
        f"Welcome! For your onboarding ({case_id}), please send these documents: "
        + "; ".join(items)
        + "."
    )


def reminder_text(case_id: str, items: list[str], number: int) -> str:
    return (
        f"Reminder {number} for {case_id}: we are still waiting for "
        + "; ".join(items)
        + "."
    )


def followup_escalation_text(case_id: str, items: list[str], hours: int) -> str:
    return (
        f"Case {case_id}: after {hours} hours and the reminders, the candidate has "
        "not delivered " + "; ".join(items) + ". Please follow up."
    )


def payroll_return_text(case_id: str) -> str:
    return f"Case {case_id}: Payroll returned an issue. A task was added to the case."


def ldc_handoff_text(case_id: str, ship_by: str) -> str:
    return (
        f"New hire in the LDC tracker ({case_id}). Please approve the welcome kit "
        f"so it ships by {ship_by}."
    )


def leader_drafts_text(case_id: str) -> str:
    return (
        f"Case {case_id} reached two months. The leader feedback request and the "
        "congratulation wait for your approval."
    )


def duplicate_text(existing_ref: str) -> str:
    return (
        "This start was not processed: a case for the same person and start date "
        f"already exists ({existing_ref})."
    )


def notify(alerts: Alerts, case_id: str, recipient: str, text: str) -> None:
    alerts.post_alert(case_id, recipient, text)
