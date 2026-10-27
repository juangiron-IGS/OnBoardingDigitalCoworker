from ..domain.errors import GovernanceError
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository


def assign_owner(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    owner: str,
    *,
    assigned_by: str,
) -> None:
    """The supervisor assigns the follow-up owner (US-032, BR-009).

    The assignment replaces the recommendation; the audit records who assigned it
    and whether the recommendation was kept or replaced.
    """
    with repo.transaction():
        repo.lock_case(case_id)
        recommended = repo.recommended_owner(case_id)
        if recommended is None:
            raise GovernanceError("no_recommendation")
        repo.assign_owner(case_id, owner)
        audit.append(
            case_id=case_id,
            agent=assigned_by,
            action="assign_owner",
            outcome="completed",
            data_refs={
                "assigned_owner": assigned_by,
                "recommended_owner": "kept" if owner == recommended else "replaced",
            },
        )
