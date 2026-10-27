"""Culture and Belonging (US-028, US-029): LDC approves the welcome kit and every
leader message before it is sent. Each change and its audit entry commit together;
a refusal is audited in its own transaction before it reaches the caller."""

from ..adapters.postgres.igs_repository import PostgresIgsRepository
from ..domain.approval_gate import Approval, verify
from ..domain.errors import GovernanceError
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository
from .decisions import APPROVED_STATES


def _refused(
    repo: CaseRepository,
    audit: AuditLog,
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


def record_kit_approval(
    repo: CaseRepository,
    igs: PostgresIgsRepository,
    audit: AuditLog,
    case_id: str,
    *,
    package_version: int,
    approved_by: str,
) -> None:
    """US-028 AC-002: LDC approves the welcome kit of the current, approved version."""
    action = "approve_welcome_kit"
    try:
        with repo.transaction():
            case = repo.lock_case(case_id)
            verify(
                Approval("pending", case_id, package_version),
                case.current_package_version,
            )
            if case.state not in APPROVED_STATES:
                raise GovernanceError("case_not_approved")
            igs.add_kit_approval(case_id, package_version, approved_by)
            audit.append(
                case_id=case_id,
                agent=approved_by,
                action=action,
                outcome="completed",
                package_version=package_version,
            )
    except GovernanceError as refusal:
        raise _refused(
            repo, audit, case_id, approved_by, action, refusal.reason
        ) from None


def prepare_info_package(
    repo: CaseRepository,
    igs: PostgresIgsRepository,
    audit: AuditLog,
    case_id: str,
    content: dict,
    *,
    agent: str,
) -> None:
    """US-031 AC-001: the package of an approved case, for the team to review."""
    action = "prepare_info_package"
    with repo.transaction():
        case = repo.lock_case(case_id)
        if case.state in APPROVED_STATES:
            igs.add_info_package(case_id, content)
            audit.append(
                case_id=case_id,
                agent=agent,
                action=action,
                outcome="completed",
                rule_ids=[s["record_id"] for s in content["sections"]],
            )
            return
    raise _refused(repo, audit, case_id, agent, action, "case_not_approved")


def send_info_package(
    repo: CaseRepository,
    igs: PostgresIgsRepository,
    audit: AuditLog,
    case_id: str,
    *,
    reviewed_by: str,
) -> dict:
    """Sent only after the Onboarding Team reviewed it (US-031 AC-001)."""
    action = "send_info_package"
    with repo.transaction():
        repo.lock_case(case_id)
        package = igs.info_package(case_id)
        if package is not None and package["status"] == "draft":
            igs.mark_info_package_sent(case_id, reviewed_by)
            audit.append(
                case_id=case_id,
                agent=reviewed_by,
                action=action,
                outcome="completed",
                rule_ids=[s["record_id"] for s in package["content"]["sections"]],
            )
            return package["content"]
    reason = "no_info_package" if package is None else "info_package_sent"
    raise _refused(repo, audit, case_id, reviewed_by, action, reason)


def draft_messages(
    repo: CaseRepository,
    igs: PostgresIgsRepository,
    audit: AuditLog,
    case_id: str,
    drafts: list[tuple[str, str, str, str]],
    *,
    agent: str,
) -> None:
    """US-029 AC-003: (kind, recipient, text, rule ID) drafts wait for LDC."""
    with repo.transaction():
        for kind, recipient, text, rule_id in drafts:
            igs.add_message(case_id, kind, recipient, text, rule_id)
        audit.append(
            case_id=case_id,
            agent=agent,
            action="draft_leader_messages",
            outcome="completed",
            rule_ids=sorted({d[3] for d in drafts}),
            data_refs={d[0]: "LDC template" for d in drafts},
        )


def approve_message(
    repo: CaseRepository,
    igs: PostgresIgsRepository,
    audit: AuditLog,
    case_id: str,
    message_id: int,
    *,
    approved_by: str,
) -> None:
    action = "approve_leader_message"
    with repo.transaction():
        repo.lock_case(case_id)
        message = igs.message(case_id, message_id)
        if message is not None and message["status"] == "draft":
            igs.set_message_status(message_id, "approved", approved_by=approved_by)
            audit.append(
                case_id=case_id,
                agent=approved_by,
                action=action,
                outcome="completed",
                data_refs={message["kind"]: "leader message"},
            )
            return
    reason = "no_message" if message is None else f"message_{message['status']}"
    raise _refused(repo, audit, case_id, approved_by, action, reason)


def mark_sent(
    repo: CaseRepository,
    igs: PostgresIgsRepository,
    audit: AuditLog,
    case_id: str,
    message_id: int,
    *,
    agent: str,
) -> dict:
    """US-029 AC-001: a message is sent only after LDC approved it."""
    action = "send_leader_message"
    with repo.transaction():
        repo.lock_case(case_id)
        message = igs.message(case_id, message_id)
        if message is not None and message["status"] == "approved":
            igs.set_message_status(message_id, "sent")
            audit.append(
                case_id=case_id,
                agent=agent,
                action=action,
                outcome="completed",
                data_refs={message["kind"]: "leader message"},
            )
            return message
    reason = "no_message" if message is None else "message_not_approved"
    raise _refused(repo, audit, case_id, agent, action, reason)
