import pytest

from services.case_service.domain.case import CaseState, transition
from services.case_service.domain.errors import GovernanceError, InvalidTransition


def test_allowed_transition_returns_new_state() -> None:
    # Arrange
    current = CaseState.VALIDATED
    # Act
    result = transition(current, CaseState.CASE_SET_UP)
    # Assert
    assert result is CaseState.CASE_SET_UP


def test_action_refused_before_approval_gate() -> None:
    # US-036 AC-001: a case in Ready for review cannot run actions
    with pytest.raises(InvalidTransition) as refusal:
        transition(CaseState.READY_FOR_REVIEW, CaseState.ACTIONS_EXECUTED)
    assert refusal.value.reason == "invalid_transition"


def test_returned_package_goes_back_to_validated() -> None:
    # US-036 AC-002: a returned package goes back to Validated
    assert transition(CaseState.APPROVAL_GATE, CaseState.VALIDATED) is (
        CaseState.VALIDATED
    )


@pytest.mark.parametrize("target", list(CaseState))
def test_rejected_case_cannot_move(target: CaseState) -> None:
    # US-013 AC-003: a rejected case stays stopped
    with pytest.raises(InvalidTransition):
        transition(CaseState.REJECTED, target)


def test_duplicate_blocks_at_received() -> None:
    assert transition(CaseState.RECEIVED, CaseState.BLOCKED_DUPLICATE) is (
        CaseState.BLOCKED_DUPLICATE
    )


def test_blocked_duplicate_cannot_move() -> None:
    with pytest.raises(InvalidTransition):
        transition(CaseState.BLOCKED_DUPLICATE, CaseState.VALIDATED)


def test_invalid_transition_is_a_governance_error() -> None:
    assert issubclass(InvalidTransition, GovernanceError)
