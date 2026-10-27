"""The status dashboard (US-030, FR-DSH-001/002): every case under its current state,
with who must act next and its risks. Read only, from the case record; it names
fields and documents, never restricted values (BR-011)."""

from datetime import date
from typing import TYPE_CHECKING

from contracts.case_service_api import CaseState

from .chat import STATE_LABELS

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

# Lifecycle order of the dashboard columns (checkpoint "Case states").
ORDER = [
    CaseState.RECEIVED,
    CaseState.NEEDS_CLARIFICATION,
    CaseState.VALIDATED,
    CaseState.CASE_SET_UP,
    CaseState.READY_FOR_REVIEW,
    CaseState.APPROVAL_GATE,
    CaseState.APPROVED,
    CaseState.ACTIONS_EXECUTED,
    CaseState.DOCUMENTS_PENDING,
    CaseState.IN_VERIFICATION,
    CaseState.SENT_TO_PAYROLL,
    CaseState.HANDOFF_TO_IGS,
    CaseState.CLOSED,
    CaseState.REJECTED,
    CaseState.BLOCKED_DUPLICATE,
]
STARTS_SOON_DAYS = 7
# What the Onboarding Team reviews before the approver decides (US-026).
REVIEWED = {"path": "onboarding path", "paperwork": "paperwork"}
BEFORE_ACTIONS = {
    CaseState.RECEIVED,
    CaseState.NEEDS_CLARIFICATION,
    CaseState.VALIDATED,
    CaseState.CASE_SET_UP,
    CaseState.READY_FOR_REVIEW,
    CaseState.APPROVAL_GATE,
}


def build(orch: "Orchestrator", *, role: str, today: date | None = None) -> list[dict]:
    """Columns in lifecycle order; only states that have cases."""
    today = today or date.today()
    columns: dict[CaseState, list[dict]] = {}
    for item in orch.cases.list_cases():
        view = orch.cases.case_view(item["id"], role=role)
        if view is None:
            continue
        state = CaseState(item["state"])
        columns.setdefault(state, []).append(
            {
                "id": item["id"],
                "person_ref": item["person_ref"],
                "start_date": item["start_date"],
                "package_version": item["package_version"],
                "pending": _pending(orch, view, state),
                "done": _done(view),
                "risks": _risks(view, state, today),
            }
        )
    return [
        {"state": s.value, "label": STATE_LABELS.get(s, s.value), "cases": columns[s]}
        for s in ORDER
        if s in columns
    ]


def _pending(orch: "Orchestrator", view: dict, state: CaseState) -> list[str]:
    case = view["case"]
    pending = []
    if state is CaseState.NEEDS_CLARIFICATION:
        labels = ", ".join(q["label"] for q in orch.questions(case["id"]))
        pending.append(f"Recruiter to answer: {labels}")
    review = case["data"].get("team_review") or {}
    if state is CaseState.READY_FOR_REVIEW:
        to_review = [name for name in REVIEWED if name not in review]
        if to_review:
            items = " and ".join(REVIEWED[name] for name in to_review)
            pending.append(f"Onboarding Team to review the {items}")
    if state in (CaseState.READY_FOR_REVIEW, CaseState.APPROVAL_GATE):
        pending.append(f"Approver to decide on package v{case['package_version']}")
    if case.get("recommended_owner") and not case.get("assigned_owner"):
        pending.append("Supervisor to assign the follow-up owner")
    lines = view["package"]["lines"] if view["package"] else []
    has_request = any(
        line["field"] == "equipment_request" and line["label"] != "exception"
        for line in lines
    )
    if (
        has_request
        and not case.get("it_approved")
        and state in BEFORE_ACTIONS | {CaseState.ACTIONS_EXECUTED}
    ):
        pending.append("IT to approve the laptop request")
    checklist = view.get("checklist", [])
    outstanding = sum(1 for c in checklist if c["status"] == "outstanding")
    to_sign = sum(1 for c in checklist if c["status"] == "pending_countersign")
    if outstanding:
        pending.append(f"Candidate to deliver {outstanding} document(s)")
    if to_sign:
        pending.append(f"Onboarding Team to countersign {to_sign} document(s)")
    if (
        state is CaseState.IN_VERIFICATION
        and checklist
        and not (outstanding or to_sign)
    ):
        pending.append("Onboarding Team to approve the payroll handoff")
    systems = {r["system"] for r in view.get("records", [])}
    if "ldc_tracker" in systems and "welcome_kits" not in systems:
        pending.append("LDC to approve the welcome kit")
    drafts = [m for m in view.get("leader_messages", []) if m["status"] == "draft"]
    if drafts:
        pending.append(f"LDC to approve {len(drafts)} leader message(s)")
    for task in view.get("payroll_returns", []):
        pending.append(f"Payroll return: {task['issue']}")
    return pending


def _done(view: dict) -> list[str]:
    """Steps already completed, so they leave the pending list (US-030)."""
    case = view["case"]
    done = []
    review = case["data"].get("team_review") or {}
    for name, label in REVIEWED.items():
        if name in review:
            how = "confirmed" if review[name].get("confirmed") else "changed"
            done.append(f"Onboarding Team {how} the {label}")
    if case.get("assigned_owner"):
        done.append(f"Follow-up owner assigned: {case['assigned_owner']}")
    if case.get("it_approved"):
        done.append("IT approved the laptop request")
    systems = {r["system"] for r in view.get("records", [])}
    if "ldc_tracker" in systems:
        done.append("Handed off to IGS: in the LDC tracker")
    if "welcome_kits" in systems:
        done.append("LDC approved the welcome kit (shipped)")
    return done


def _risks(view: dict, state: CaseState, today: date) -> list[str]:
    case = view["case"]
    risks = []
    lines = view["package"]["lines"] if view["package"] else []
    exceptions = [line for line in lines if line["label"] == "exception"]
    if view["package"] and view["package"]["status"] != "ready":
        risks.append(f"Package blocked: {len(exceptions)} exception(s)")
    elif exceptions:
        risks.append(f"{len(exceptions)} exception(s) to review")
    days = (date.fromisoformat(case["start_date"]) - today).days
    if state in BEFORE_ACTIONS and days <= STARTS_SOON_DAYS:
        risks.append(
            "Start date passed"
            if days < 0
            else f"Starts in {days} day(s), not approved"
        )
    timing = case.get("package_timing")
    if timing and not timing["met"]:
        risks.append("Package missed the 5-minute target")
    escalated = any(r["kind"] == "escalation" for r in view.get("reminders", []))
    if escalated and state is CaseState.DOCUMENTS_PENDING:
        risks.append("Documents escalated after the reminders")
    if state is CaseState.BLOCKED_DUPLICATE:
        risks.append("Duplicate start: blocked")
    return risks
