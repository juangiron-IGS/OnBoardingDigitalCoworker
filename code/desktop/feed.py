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
    """The web app opened as the tray's role, on the alert's case in Status."""
    base = f"{base.rstrip('/')}/?role={role}"
    return f"{base}#status/{case_id}" if case_id else f"{base}#dashboard"


def title(alert: dict) -> str:
    return f"Onboarding Coworker · {alert.get('case_id') or 'alert'}"
