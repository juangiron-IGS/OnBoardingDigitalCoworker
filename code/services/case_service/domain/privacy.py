"""Who may see restricted data (BR-011, US-040). The front end never decides this.

The authorized roles are a default pending confirmation (OQ-003).
"""

import re

ROLES = frozenset({"recruiter", "onboarding", "approver", "it", "ldc"})
RESTRICTED_FIELDS = frozenset({"flsa", "sponsorship_visa"})
AUTHORIZED_ROLES = frozenset({"onboarding", "approver"})
HIDDEN = "Restricted"

# Words that mark FLSA, sponsorship, visa or work-authorization content (BR-011).
# Text that matches never reaches a prompt, a log or a stored question.
RESTRICTED_TERMS = (
    r"flsa|exempt|sponsor\w*|visa|h-?1-?b|green[- ]?card|work (permit|authori[sz]ation)"
    r"|\b(opt|ead|tn|l-?1|o-?1)\b|citizen\w*|permanent resident|immigra\w*"
)


def can_see_restricted(role: str) -> bool:
    return role in AUTHORIZED_ROLES


_RESTRICTED_VALUE = re.compile(RESTRICTED_TERMS, re.IGNORECASE)


def reveals_restricted(value: object) -> bool:
    """A value that names an FLSA, visa or sponsorship status, such as a form
    called "Non-exempt employee agreement" (BR-011)."""
    return bool(_RESTRICTED_VALUE.search(str(value or "")))


def redact(data: dict[str, object], role: str) -> dict[str, object]:
    if can_see_restricted(role):
        return dict(data)
    return {k: HIDDEN if k in RESTRICTED_FIELDS and v else v for k, v in data.items()}
