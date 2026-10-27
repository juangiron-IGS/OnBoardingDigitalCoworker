"""After approval: the candidate checklist and reminders (US-022), the document check
with the Onboarding Team's countersign (US-023) and the payroll handoff and returns
(US-024). Each change and its audit entry commit in one transaction; a refusal is
audited in its own transaction before it reaches the caller."""

from ..adapters.postgres.followup_repository import PostgresFollowupRepository
from ..domain.approval_gate import Approval, verify
from ..domain.case import CaseState, transition
from ..domain.errors import GovernanceError
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository


def _move(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    current: CaseState,
    target: CaseState,
    agent: str,
) -> None:
    repo.set_state(case_id, transition(current, target))
    audit.append(
        case_id=case_id,
        agent=agent,
        action="transition",
        outcome="completed",
        data_refs={"from": current.value, "to": target.value},
    )


def _refused(
    audit: AuditLog,
    repo: CaseRepository,
    case_id: str,
    agent: str,
    action: str,
    reason: str,
) -> GovernanceError:
    with repo.transaction():
        audit.append(
            case_id=case_id,
            agent=agent,
            action=action,
            outcome="refused",
            data_refs={"reason": reason},
        )
    return GovernanceError(reason)


def send_checklist(
    repo: CaseRepository,
    followup: PostgresFollowupRepository,
    audit: AuditLog,
    case_id: str,
    items: list[tuple[str, str]],
    *,
    agent: str,
) -> None:
    """US-022 AC-001: the checklist of an approved case, which then waits for
    documents."""
    with repo.transaction():
        case = repo.lock_case(case_id)
        followup.add_items(case_id, items)
        audit.append(
            case_id=case_id,
            agent=agent,
            action="send_checklist",
            outcome="completed",
            rule_ids=sorted({r for _, r in items if r.startswith("R-")}),
            data_refs={item: required_by for item, required_by in items},
        )
        _move(repo, audit, case_id, case.state, CaseState.DOCUMENTS_PENDING, agent)


def record_reminder(
    repo: CaseRepository,
    followup: PostgresFollowupRepository,
    audit: AuditLog,
    case_id: str,
    *,
    kind: str,
    at_hours: int,
    rule_id: str,
    agent: str,
) -> None:
    with repo.transaction():
        followup.add_reminder(case_id, kind, at_hours, rule_id)
        audit.append(
            case_id=case_id,
            agent=agent,
            action=f"send_{kind}",
            outcome="completed",
            rule_ids=[rule_id],
            data_refs={"at_hours": str(at_hours)},
        )


def record_delivery(
    repo: CaseRepository,
    followup: PostgresFollowupRepository,
    audit: AuditLog,
    case_id: str,
    items: list[str],
    *,
    recorded_by: str,
) -> list[str]:
    """US-023 AC-001: delivered items wait for the countersign; returns what is
    still missing. When nothing is missing the case moves to In verification."""
    action = "record_delivery"
    with repo.transaction():
        case = repo.lock_case(case_id)
        if case.state not in (CaseState.DOCUMENTS_PENDING, CaseState.IN_VERIFICATION):
            reason = "case_not_waiting_for_documents"
        else:
            checklist = {c["item"]: c["status"] for c in followup.checklist(case_id)}
            unknown = [i for i in items if i not in checklist]
            if unknown:
                raise ValueError(f"not on the checklist: {', '.join(unknown)}")
            for item in items:
                if checklist[item] == "outstanding":
                    followup.set_status(case_id, item, "pending_countersign")
                    checklist[item] = "pending_countersign"
            missing = [i for i, s in checklist.items() if s == "outstanding"]
            audit.append(
                case_id=case_id,
                agent=recorded_by,
                action=action,
                outcome="completed",
                data_refs={item: "candidate" for item in items},
            )
            if not missing and case.state is CaseState.DOCUMENTS_PENDING:
                _move(
                    repo,
                    audit,
                    case_id,
                    case.state,
                    CaseState.IN_VERIFICATION,
                    recorded_by,
                )
            return missing
    raise _refused(audit, repo, case_id, recorded_by, action, reason)


def countersign(
    repo: CaseRepository,
    followup: PostgresFollowupRepository,
    audit: AuditLog,
    case_id: str,
    item: str,
    *,
    signed_by: str,
) -> None:
    """US-023 AC-002: a document is verified only when the Onboarding Team signs."""
    action = "countersign_document"
    with repo.transaction():
        repo.lock_case(case_id)
        status = {c["item"]: c["status"] for c in followup.checklist(case_id)}.get(item)
        if status == "pending_countersign":
            followup.set_status(case_id, item, "verified", verified_by=signed_by)
            audit.append(
                case_id=case_id,
                agent=signed_by,
                action=action,
                outcome="completed",
                data_refs={item: "checklist"},
            )
            return
    raise _refused(
        audit,
        repo,
        case_id,
        signed_by,
        action,
        "not_on_checklist" if status is None else f"document_{status}",
    )


def approve_payroll_handoff(
    repo: CaseRepository,
    followup: PostgresFollowupRepository,
    audit: AuditLog,
    case_id: str,
    *,
    package_version: int,
    approved_by: str,
) -> None:
    """US-024 (FR-PAY-002): the Onboarding Team approves the handoff of the current
    version once every document is verified."""
    action = "approve_payroll_handoff"
    try:
        with repo.transaction():
            case = repo.lock_case(case_id)
            verify(
                Approval("pending", case_id, package_version),
                case.current_package_version,
            )
            if case.state is not CaseState.IN_VERIFICATION:
                raise GovernanceError("case_not_in_verification")
            if any(c["status"] != "verified" for c in followup.checklist(case_id)):
                raise GovernanceError("documents_not_verified")
            followup.add_payroll_handoff(case_id, package_version, approved_by)
            audit.append(
                case_id=case_id,
                agent=approved_by,
                action=action,
                outcome="completed",
                package_version=package_version,
            )
    except GovernanceError as refusal:
        raise _refused(
            audit, repo, case_id, approved_by, action, refusal.reason
        ) from None


def record_payroll_return(
    repo: CaseRepository,
    followup: PostgresFollowupRepository,
    audit: AuditLog,
    case_id: str,
    issue: str,
    *,
    agent: str,
) -> int:
    """US-024 AC-003: an issue Payroll returns becomes a task on the case."""
    with repo.transaction():
        case = repo.lock_case(case_id)
        if case.state is not CaseState.SENT_TO_PAYROLL:
            reason = "case_not_sent_to_payroll"
        else:
            task_id = followup.add_payroll_return(case_id, issue)
            audit.append(
                case_id=case_id,
                agent=agent,
                action="payroll_return",
                outcome="completed",
                data_refs={"task": f"payroll-return-{task_id}"},
            )
            return task_id
    raise _refused(audit, repo, case_id, agent, "payroll_return", reason)
