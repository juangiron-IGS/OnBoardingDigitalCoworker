from ..domain.case import CaseState, transition
from ..domain.errors import GovernanceError
from ..domain.package import PackageLine, package_status
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository


def build_package(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    lines: list[PackageLine],
    *,
    agent: str,
    escalated: bool = False,
    waiting_answer: bool = False,
) -> int:
    """Store a new package version and move the case to Ready for review.

    Only a case in Case set up, which passed the checks, gets a package (US-011
    AC-003). Every change produces a new version; earlier ones are kept (US-012).
    """
    with repo.transaction():
        case = repo.lock_case(case_id)
        if case.state is not CaseState.CASE_SET_UP:
            raise GovernanceError("case_not_ready")
        version = case.current_package_version + 1
        status = package_status(escalated=escalated, waiting_answer=waiting_answer)
        repo.add_package_version(case_id, version, status, lines)
        repo.set_state(case_id, transition(case.state, CaseState.READY_FOR_REVIEW))
        audit.append(
            case_id=case_id,
            agent=agent,
            action="build_package",
            outcome="completed",
            package_version=version,
            rule_ids=sorted(
                {line.source_or_rule_id for line in lines if line.label != "source"}
            ),
            data_refs={line.field: line.source_or_rule_id for line in lines},
        )
    return version
