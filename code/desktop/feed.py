"""What the tray shows: only alerts it has not shown yet, and where each one opens.
No I/O here, so the rules are easy to test."""

from dataclasses import dataclass, field

ROLES = {
    "recruiter": "Recruiter",
    "onboarding": "Onboarding Team",
    "approver": "Approver",
    "it": "IT",
    "ldc": "LDC (Culture and Belonging)",
    "all": "All teams",
}
ALL = "all"
# The role whose view each team's alert opens, so "All teams" opens the right one.
RECIPIENT_ROLE = {
    "Recruiter": "recruiter",
    "Onboarding Team": "onboarding",
    "HR": "onboarding",
    "Onboarding Supervisor": "approver",
    "IT": "it",
    "LDC": "ldc",
}
# Each team's alert in a notification: who it is for, the step of the flow, the
# button and the view it opens on the case.
ACTIONS = {
    "Recruiter": (
        "Recruiter",
        "Intake · complete the start data",
        "Answer in the chat",
        "chat",
    ),
    "Onboarding Team": (
        "Onboarding Team",
        "Follow-up · documents or payroll",
        "Open in Status",
        "status",
    ),
    "HR": (
        "HR (through the Onboarding Team)",
        "HR decision · FLSA or classification",
        "Record HR's answer",
        "approval",
    ),
    "Onboarding Supervisor": (
        "Approver",
        "Approval gate · assign the owner and decide",
        "Open the package",
        "approval",
    ),
    "IT": (
        "IT",
        "Equipment · approve the laptop and access request",
        "Review the request",
        "approval",
    ),
    "LDC": (
        "LDC (Culture and Belonging)",
        "Culture and Belonging · welcome kit and leader messages",
        "Open in Approval",
        "approval",
    ),
}


def action(alert: dict) -> tuple[str, str, str, str]:
    """(team, step, button, view) for an alert; review and FLSA alerts open Approval."""
    team, step, button, view = ACTIONS.get(
        alert.get("recipient", ""),
        ("your team", "Onboarding alert", "Open case", "chat"),
    )
    text = alert.get("text", "")
    if team == "Onboarding Team" and "ready" in text:
        return (
            team,
            "Review · confirm or change the path and paperwork",
            "Review the package",
            "approval",
        )
    if team == "Onboarding Team" and "differs" in text:
        return (
            team,
            "HR decision · FLSA or classification",
            "Record HR's answer",
            "approval",
        )
    return team, step, button, view


THEMES = {"system": "Same as Windows", "light": "Light", "dark": "Dark"}

BYLINE = "By INSPYR Velocity - All rights reserved"
ABOUT = (
    "Onboarding Coworker\n"
    f"{BYLINE}\n\n"
    "A digital coworker for the INSPYR onboarding team. It reads each new start "
    "from the recruiter's email, asks the recruiter for any missing data, and "
    "builds the onboarding package: path, paperwork, welcome kit, owner and the "
    "laptop and access request, each line with its source or rule.\n\n"
    "People decide: the Onboarding Team reviews, IT approves equipment and the "
    "Consultant Onboarding Supervisor approves the package before anything is "
    "created in the (simulated) systems. It then follows up the candidate's "
    "documents, the payroll handoff and the IGS welcome. FLSA, classification "
    "and legal questions go to HR.\n\n"
    "Specialized agents work on one case under an orchestrator. Every action is "
    "audited. Synthetic data only."
)


@dataclass
class AlertFeed:
    """Tracks the newest alert already seen. The first poll only sets the mark, so
    starting the tray never floods the screen with old alerts."""

    last_id: int | None = None
    recent: list[dict] = field(default_factory=list)
    unseen: int = 0

    def new(self, alerts: list[dict]) -> list[dict]:
        """Alerts newer than the mark, oldest first; also keeps the 5 latest."""
        ordered = sorted(alerts, key=lambda a: a["id"])
        if ordered:
            self.recent = list(reversed(ordered[-5:]))
        if self.last_id is None:
            self.last_id = ordered[-1]["id"] if ordered else 0
            return []
        fresh = [a for a in ordered if a["id"] > self.last_id]
        if fresh:
            self.last_id = fresh[-1]["id"]
            self.unseen += len(fresh)
        return fresh

    def mark_seen(self) -> None:
        self.unseen = 0

    def reset(self) -> None:
        """A new role sees its own alerts from now on."""
        self.last_id, self.recent, self.unseen = None, [], 0


def case_url(base: str, case_id: str | None, role: str) -> str:
    """The web app in the browser, as the tray's role, on the case in Status."""
    base = f"{base.rstrip('/')}/?role={role}"
    return f"{base}#status/{case_id}" if case_id else f"{base}#dashboard"


def window_url(
    base: str,
    case_id: str | None,
    role: str,
    theme: str = "system",
    view: str = "chat",
) -> str:
    """The Coworker window on the alert's case: the chat, or the view it asks for."""
    base = f"{base.rstrip('/')}/?role={role}&mode=desktop"
    if theme in ("light", "dark"):
        base += f"&theme={theme}"
    return f"{base}#{view}/{case_id}" if case_id else f"{base}#{view}"
