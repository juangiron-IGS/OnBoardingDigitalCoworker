from ..domain.approval_gate import Approval, verify
from ..domain.errors import GovernanceError
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository

ACTION = "approve_it_request"


def record_it_approval(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    *,
    package_version: int,
    approver_role: str,
) -> None:
    """IT approves the access and laptop request of the current version (US-020,
    BR-012). The request is sent only when the approver has approved it too."""
    try:
        with repo.transaction():
            case = repo.lock_case(case_id)
            verify(
                Approval("pending", case_id, package_version),
                case.current_package_version,
            )
            if not repo.has_line(case_id, package_version, "equipment_request"):
                raise GovernanceError("no_it_request")
            repo.add_it_approval(case_id, package_version, approver_role)
            audit.append(
                case_id=case_id,
                agent=approver_role,
                action=ACTION,
                outcome="completed",
                package_version=package_version,
            )
    except GovernanceError:
        # Its own transaction, so the refusal is kept even if the caller rolls back.
        with repo.transaction():
            audit.append(
                case_id=case_id,
                agent=approver_role,
                action=ACTION,
                outcome="refused",
                package_version=package_version,
            )
        raise
