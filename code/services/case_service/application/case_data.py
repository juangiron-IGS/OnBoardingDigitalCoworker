from typing import Any

from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository


def record_answers(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    values: dict[str, Any],
    *,
    agent: str,
    source: str,
) -> None:
    """Merge confirmed values into the case and audit which fields came from where.

    The audit names the fields only, never their values (BR-011).
    """
    with repo.transaction():
        repo.lock_case(case_id)
        repo.merge_case_data(case_id, values)
        audit.append(
            case_id=case_id,
            agent=agent,
            action="record_answers",
            outcome="completed",
            data_refs={field: source for field in values},
        )


def log_action(
    repo: CaseRepository,
    audit: AuditLog,
    case_id: str,
    *,
    agent: str,
    action: str,
    outcome: str = "completed",
    rule_ids: list[str] | None = None,
    data_refs: dict[str, str] | None = None,
) -> None:
    """Audit an agent action that changes no case data (US-018)."""
    with repo.transaction():
        audit.append(
            case_id=case_id,
            agent=agent,
            action=action,
            outcome=outcome,
            rule_ids=rule_ids,
            data_refs=data_refs,
        )
