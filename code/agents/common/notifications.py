"""Shared notifications tool (not an agent): wording per audience, sent through the
Teams mock. Messages name fields, never restricted values (BR-011), and name a case
by its candidate and role ("SYN-0043 · QA Engineer"), never its internal ID."""

from contracts.mcp_tools import Alerts


def label(field: str, labels: dict[str, list[str]]) -> str:
    return labels.get(field, [field])[0]


def missing_fields_text(
    case: str,
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
    return f"{case} needs your answer. " + " ".join(parts)


def escalation_text(case: str, fields: list[str], labels: dict[str, list[str]]) -> str:
    names = ", ".join(label(f, labels) for f in fields)
    return (
        f"{case}: {names} differs between the start email and the JobDiva "
        "start notes. It is escalated for your decision; the Coworker has not chosen "
        "a value."
    )


def owner_text(case: str, owner: str, rule_id: str) -> str:
    return (
        f"New hire {case}. Recommended follow-up owner: {owner} "
        f"({rule_id}). Please assign the owner in the approval view."
    )


def review_text(case: str) -> str:
    return (
        f"Package v1 for {case} is ready. Please confirm or change the recommended "
        "onboarding path and paperwork before the approver decides."
    )


def it_request_text(case: str, package_version: int) -> str:
    return (
        f"{case}: package v{package_version} is approved. The laptop and "
        "access request waits for your approval in the approval view."
    )


def checklist_text(case: str, items: list[str]) -> str:
    return (
        f"Welcome! For your onboarding ({case}), please send these documents: "
        + "; ".join(items)
        + "."
    )


def checklist_email(case: str, items: list[str]) -> dict:
    """The checklist as the email the candidate receives (simulated, US-022)."""
    return {
        "to": "Candidate (synthetic mailbox)",
        "subject": f"Welcome to INSPYR: documents for your onboarding ({case})",
        "body": [
            "Hello,",
            f"Welcome to INSPYR! To complete your onboarding ({case}), please send "
            "us these documents:",
            *[f"- {item}" for item in items],
            "Reply to this email with the documents attached. If something is "
            "still missing, we will send you a reminder.",
            "Thank you,",
            "INSPYR Onboarding Team",
        ],
    }


def reminder_text(case: str, items: list[str], number: int) -> str:
    return (
        f"Reminder {number} for {case}: we are still waiting for "
        + "; ".join(items)
        + "."
    )


def followup_escalation_text(case: str, items: list[str], hours: int) -> str:
    return (
        f"{case}: after {hours} hours and the reminders, the candidate has "
        "not delivered " + "; ".join(items) + ". Please follow up."
    )


def payroll_return_text(case: str) -> str:
    return f"{case}: Payroll returned an issue. A task was added to the case."


def ldc_handoff_text(case: str, ship_by: str) -> str:
    return (
        f"New hire in the LDC tracker ({case}). Please approve the welcome kit "
        f"so it ships by {ship_by}."
    )


def leader_drafts_text(case: str) -> str:
    return (
        f"{case} reached two months. The leader feedback request and the "
        "congratulation wait for your approval."
    )


def info_package_text(case: str, sections: list[dict]) -> str:
    parts = " ".join(f"{s['heading']}: {s['text']}" for s in sections)
    return f"Your welcome information ({case}). {parts}"


def duplicate_text(existing_ref: str) -> str:
    return (
        "This start was not processed: a case for the same person and start date "
        f"already exists ({existing_ref})."
    )


def notify(alerts: Alerts, case_id: str, recipient: str, text: str) -> None:
    alerts.post_alert(case_id, recipient, text)
