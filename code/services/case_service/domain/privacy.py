"""Who may see restricted data (BR-011, US-040). The front end never decides this.

The authorized roles are a default pending confirmation (OQ-003).
"""

ROLES = frozenset({"recruiter", "onboarding", "approver", "it", "ldc"})
RESTRICTED_FIELDS = frozenset({"flsa", "sponsorship_visa"})
AUTHORIZED_ROLES = frozenset({"onboarding", "approver"})
HIDDEN = "Restricted"


def can_see_restricted(role: str) -> bool:
    return role in AUTHORIZED_ROLES


def redact(data: dict[str, object], role: str) -> dict[str, object]:
    if can_see_restricted(role):
        return dict(data)
    return {k: HIDDEN if k in RESTRICTED_FIELDS and v else v for k, v in data.items()}
