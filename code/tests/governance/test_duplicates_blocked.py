import os
import uuid
from datetime import date

import psycopg
import pytest

from services.case_service.adapters.postgres.audit_log import PostgresAuditLog
from services.case_service.adapters.postgres.case_repository import (
    PostgresCaseRepository,
)
from services.case_service.application.create_case import CaseIntake, create_case
from services.case_service.domain.case import CaseState
from services.case_service.domain.errors import DuplicateCase

pytestmark = pytest.mark.db

START = date(2026, 11, 2)


class FakeJobDivaRead:
    def __init__(self, start_id: str | None = None) -> None:
        self._start_id = start_id

    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        return {"found": self._start_id is not None, "start_id": self._start_id}


@pytest.fixture
def person_ref() -> str:
    return f"person-{uuid.uuid4()}"


def _create(app_conn, person_ref: str, jobdiva: FakeJobDivaRead | None = None) -> str:
    return create_case(
        PostgresCaseRepository(app_conn),
        PostgresAuditLog(app_conn),
        jobdiva or FakeJobDivaRead(),
        CaseIntake(person_ref=person_ref, start_date=START, data={"role": "Analyst"}),
        agent="intake_validation",
    )


def test_new_start_creates_case_in_received_and_is_audited(
    app_conn, person_ref
) -> None:
    case_id = _create(app_conn, person_ref)

    state = app_conn.execute(
        "SELECT state FROM cases WHERE id = %s", (case_id,)
    ).fetchone()[0]
    entry = app_conn.execute(
        "SELECT agent, action, outcome FROM audit_log WHERE case_id = %s", (case_id,)
    ).fetchone()
    assert state == CaseState.RECEIVED
    assert entry == ("intake_validation", "create_case", "completed")


def test_second_start_same_person_and_date_is_blocked_at_received(
    app_conn, person_ref
) -> None:
    # US-017 AC-001: no new case is created
    first = _create(app_conn, person_ref)

    with pytest.raises(DuplicateCase):
        _create(app_conn, person_ref)

    count = app_conn.execute(
        "SELECT count(*) FROM cases WHERE person_ref = %s", (person_ref,)
    ).fetchone()[0]
    refusal = app_conn.execute(
        "SELECT outcome FROM audit_log WHERE case_id = %s AND action = 'create_case'"
        " ORDER BY id DESC LIMIT 1",
        (first,),
    ).fetchone()[0]
    assert count == 1
    assert refusal == "refused"


def test_block_message_names_existing_case(app_conn, person_ref) -> None:
    # US-017 AC-002: the message identifies the existing case
    first = _create(app_conn, person_ref)

    with pytest.raises(DuplicateCase) as blocked:
        _create(app_conn, person_ref)

    assert blocked.value.existing_ref == first
    assert first in str(blocked.value.message)


def test_duplicate_found_in_jobdiva_also_blocks(app_conn, person_ref) -> None:
    # US-017 AC-001: a start already in JobDiva is a duplicate too
    with pytest.raises(DuplicateCase) as blocked:
        _create(app_conn, person_ref, FakeJobDivaRead(start_id="JD-START-77"))

    count = app_conn.execute(
        "SELECT count(*) FROM cases WHERE person_ref = %s", (person_ref,)
    ).fetchone()[0]
    assert count == 0
    assert blocked.value.existing_ref == "jobdiva:JD-START-77"


def test_refusal_is_committed_on_its_own(person_ref) -> None:
    # US-018 AC-002: the refusal is committed even though the start is refused.
    # Uses a real committed connection, so it leaves synthetic rows behind.
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        first = _create(conn, person_ref)
        with pytest.raises(DuplicateCase):
            _create(conn, person_ref)

    with psycopg.connect(os.environ["DATABASE_URL"]) as reader:
        outcomes = reader.execute(
            "SELECT outcome FROM audit_log"
            " WHERE case_id = %s AND action = 'create_case' ORDER BY id",
            (first,),
        ).fetchall()
    assert outcomes == [("completed",), ("refused",)]
