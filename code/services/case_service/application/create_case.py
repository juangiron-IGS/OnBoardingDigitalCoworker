import uuid
from datetime import date
from typing import Any

import psycopg
from pydantic import BaseModel, Field

from ..domain.errors import DuplicateCase
from ..ports.audit_log import AuditLog
from ..ports.case_repository import CaseRepository
from ..ports.duplicate_search import DuplicateSearch


class CaseIntake(BaseModel):
    person_ref: str = Field(min_length=1, max_length=128)
    start_date: date
    data: dict[str, Any] = Field(default_factory=dict)


def create_case(
    repo: CaseRepository,
    audit: AuditLog,
    jobdiva_read: DuplicateSearch,
    intake: CaseIntake,
    *,
    agent: str,
) -> str:
    """Create a case in Received, or block a duplicate start (BR-004, US-017)."""
    existing = _find_duplicate(repo, jobdiva_read, intake)
    if existing:
        _refuse(repo, audit, existing, agent)

    case_id = f"case-{uuid.uuid4().hex[:12]}"
    try:
        with repo.transaction():
            repo.insert_case(case_id, intake.person_ref, intake.start_date, intake.data)
            audit.append(
                case_id=case_id,
                agent=agent,
                action="create_case",
                outcome="completed",
                data_refs={field: "intake" for field in intake.data},
            )
    except psycopg.errors.UniqueViolation:
        # A concurrent start for the same person and date won the race.
        existing = repo.find_case_id(intake.person_ref, intake.start_date)
        _refuse(repo, audit, existing or "unknown", agent)
    return case_id


def _find_duplicate(
    repo: CaseRepository, jobdiva_read: DuplicateSearch, intake: CaseIntake
) -> str | None:
    case_id = repo.find_case_id(intake.person_ref, intake.start_date)
    if case_id:
        return case_id
    found = jobdiva_read.search_duplicate(intake.person_ref, intake.start_date)
    return f"jobdiva:{found['start_id']}" if found["found"] else None


def _refuse(
    repo: CaseRepository, audit: AuditLog, existing_ref: str, agent: str
) -> None:
    # Its own transaction, so the refusal is kept even if the caller rolls back.
    with repo.transaction():
        audit.append(
            case_id=existing_ref,
            agent=agent,
            action="create_case",
            outcome="refused",
            data_refs={"person_ref": "intake", "start_date": "intake"},
        )
    raise DuplicateCase(existing_ref)
