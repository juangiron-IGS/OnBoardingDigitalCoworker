import uuid

from ..domain.approval_gate import Approval, verify
from ..domain.case import CaseState, transition
from ..domain.errors import ApprovalRefused, GovernanceError
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository

_ACTIONS = {
    "approve": "approve_package",
    "return": "return_package",
    "reject": "reject_case",
}
_TARGETS = {
    "approve": CaseState.APPROVED,
    "return": CaseState.VALIDATED,
    "reject": CaseState.REJECTED,
}


def record_approval(
    repo: CaseRepository,
    audit: AuditLog,
    *,
    case_id: str,
    package_version: int,
    approver_role: str,
    comment: str | None = None,
) -> str:
    """Approve the current package version and issue an approval ID (US-014)."""
    approval_id = f"apr-{uuid.uuid4().hex[:12]}"
    _decide(
        repo,
        audit,
        "approve",
        case_id,
        package_version,
        approver_role,
        comment,
        approval_id,
    )
    return approval_id


def return_package(
    repo: CaseRepository,
    audit: AuditLog,
    *,
    case_id: str,
    package_version: int,
    approver_role: str,
    comment: str | None = None,
) -> None:
    """Return for correction: the case goes back to Validated, no approval ID."""
    _decide(repo, audit, "return", case_id, package_version, approver_role, comment)


def reject_case(
    repo: CaseRepository,
    audit: AuditLog,
    *,
    case_id: str,
    package_version: int,
    approver_role: str,
    comment: str | None = None,
) -> None:
    """Reject: the case stops for good, no approval ID (US-013 AC-003)."""
    _decide(repo, audit, "reject", case_id, package_version, approver_role, comment)


def authorize_action(repo: CaseRepository, *, approval_id: str) -> Approval:
    """Return the approval only if it is for the case's current package version.

    Used by the JobDiva and Workflow server before every simulated action (BR-002).
    """
    approval = repo.find_approval(approval_id)
    if approval is None:
        raise ApprovalRefused("no_approval")
    case = repo.lock_case(approval.case_id)
    verify(approval, case.current_package_version)
    if case.state not in (CaseState.APPROVED, CaseState.ACTIONS_EXECUTED):
        raise ApprovalRefused("case_not_approved")
    return approval


def _decide(
    repo: CaseRepository,
    audit: AuditLog,
    decision: str,
    case_id: str,
    package_version: int,
    approver_role: str,
    comment: str | None,
    approval_id: str | None = None,
) -> None:
    action = _ACTIONS[decision]
    try:
        with repo.transaction():
            case = repo.lock_case(case_id)
            if package_version != case.current_package_version:
                raise ApprovalRefused("version_mismatch")
            if decision == "approve" and (
                repo.package_status(case_id, package_version) != "ready"
            ):
                raise GovernanceError("package_not_ready")
            state = case.state
            if state is CaseState.READY_FOR_REVIEW:
                state = transition(state, CaseState.APPROVAL_GATE)
            repo.set_state(case_id, transition(state, _TARGETS[decision]))
            repo.add_decision(
                case_id, package_version, decision, approval_id, approver_role, comment
            )
            audit.append(
                case_id=case_id,
                agent=approver_role,
                action=action,
                outcome="completed",
                approval_id=approval_id,
                package_version=package_version,
            )
    except GovernanceError:
        audit.append(
            case_id=case_id,
            agent=approver_role,
            action=action,
            outcome="refused",
            package_version=package_version,
        )
        raise
