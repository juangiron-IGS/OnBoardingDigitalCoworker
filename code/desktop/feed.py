"""What the tray shows: only alerts it has not shown yet, and where each one opens.
No I/O here, so the rules are easy to test."""

from dataclasses import dataclass, field

ROLES = {
    "recruiter": "Recruiter",
    "onboarding": "Onboarding Team",
    "approver": "Approver",
    "it": "IT",
    "ldc": "LDC (Culture and Belonging)",
}
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


def window_url(base: str, case_id: str | None, role: str, theme: str = "system") -> str:
    """The Coworker window: the chat as its main view, on the alert's case."""
    base = f"{base.rstrip('/')}/?role={role}&mode=desktop"
    if theme in ("light", "dark"):
        base += f"&theme={theme}"
    return f"{base}#chat/{case_id}" if case_id else f"{base}#chat"
