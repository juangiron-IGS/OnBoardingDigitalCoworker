class GovernanceError(Exception):
    """Base class for refusals that are expected, audited outcomes."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ApprovalRefused(GovernanceError):
    """reason: "no_approval" | "version_mismatch" (BR-002)."""


class DuplicateCase(GovernanceError):
    """Same person and start date already exist (BR-004). Blocked at Received."""

    def __init__(self, existing_ref: str) -> None:
        super().__init__("duplicate")
        self.existing_ref = existing_ref
        self.message = (
            f"A case for this person and start date already exists: {existing_ref}"
        )


class InvalidTransition(GovernanceError):
    """A case state change that is not listed in ALLOWED (US-036)."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__("invalid_transition")
        self.current = current
        self.target = target
