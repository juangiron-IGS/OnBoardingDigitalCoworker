from enum import StrEnum

from .errors import InvalidTransition


class CaseState(StrEnum):
    RECEIVED = "received"
    BLOCKED_DUPLICATE = "blocked_duplicate"
    VALIDATED = "validated"
    NEEDS_CLARIFICATION = "needs_clarification"
    CASE_SET_UP = "case_set_up"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVAL_GATE = "approval_gate"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIONS_EXECUTED = "actions_executed"
    DOCUMENTS_PENDING = "documents_pending"  # Should
    IN_VERIFICATION = "in_verification"  # Should
    SENT_TO_PAYROLL = "sent_to_payroll"  # Should
    HANDOFF_TO_IGS = "handoff_to_igs"  # Could
    CLOSED = "closed"


# Checkpoint "Case states". APPROVAL_GATE -> VALIDATED is a returned package.
# ACTIONS_EXECUTED and SENT_TO_PAYROLL may close directly while the Should and
# Could features are switched off.
ALLOWED: dict[CaseState, frozenset[CaseState]] = {
    CaseState.RECEIVED: frozenset({CaseState.VALIDATED, CaseState.BLOCKED_DUPLICATE}),
    CaseState.VALIDATED: frozenset(
        {CaseState.CASE_SET_UP, CaseState.NEEDS_CLARIFICATION}
    ),
    CaseState.NEEDS_CLARIFICATION: frozenset({CaseState.VALIDATED}),
    CaseState.CASE_SET_UP: frozenset({CaseState.READY_FOR_REVIEW}),
    # Back to Case set up when HR answers a conflict or the team changes the
    # recommendation (US-026, US-027): the package is rebuilt as a new version.
    CaseState.READY_FOR_REVIEW: frozenset(
        {CaseState.APPROVAL_GATE, CaseState.CASE_SET_UP}
    ),
    CaseState.APPROVAL_GATE: frozenset(
        {CaseState.APPROVED, CaseState.REJECTED, CaseState.VALIDATED}
    ),
    CaseState.APPROVED: frozenset({CaseState.ACTIONS_EXECUTED}),
    CaseState.ACTIONS_EXECUTED: frozenset(
        {CaseState.DOCUMENTS_PENDING, CaseState.CLOSED}
    ),
    CaseState.DOCUMENTS_PENDING: frozenset({CaseState.IN_VERIFICATION}),
    CaseState.IN_VERIFICATION: frozenset({CaseState.SENT_TO_PAYROLL}),
    CaseState.SENT_TO_PAYROLL: frozenset({CaseState.HANDOFF_TO_IGS, CaseState.CLOSED}),
    CaseState.HANDOFF_TO_IGS: frozenset({CaseState.CLOSED}),
}


def transition(current: CaseState, target: CaseState) -> CaseState:
    """Return the target state, or raise InvalidTransition if it is not allowed."""
    if target not in ALLOWED.get(current, frozenset()):
        raise InvalidTransition(current, target)
    return target
