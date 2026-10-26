from ..domain.case import CaseState, transition
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository


def move_case(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    target: CaseState,
    *,
    agent: str,
) -> CaseState:
    """Move a case to an allowed state and log the transition (US-036 AC-003)."""
    with repo.transaction():
        current = repo.lock_case(case_id).state
        new_state = transition(current, target)
        repo.set_state(case_id, new_state)
        audit.append(
            case_id=case_id,
            agent=agent,
            action="transition",
            outcome="completed",
            data_refs={"from": current.value, "to": new_state.value},
        )
    return new_state
