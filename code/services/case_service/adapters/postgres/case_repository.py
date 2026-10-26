from contextlib import AbstractContextManager
from datetime import date
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from ...domain.approval_gate import Approval
from ...domain.case import CaseState
from ...domain.errors import GovernanceError
from ...domain.package import PackageLine
from ...ports.case_repository import CaseRow


class PostgresCaseRepository:
    """Case store on the caller's connection, so writes share its transaction.

    The connection must be in autocommit mode: each use case opens its own
    transactions with transaction(), and a refusal is audited in its own
    transaction so it is kept when the refused change is rolled back.
    """

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def transaction(self) -> AbstractContextManager[Any]:
        return self._conn.transaction()

    def find_case_id(self, person_ref: str, start_date: date) -> str | None:
        row = self._conn.execute(
            "SELECT id FROM cases WHERE person_ref = %s AND start_date = %s",
            (person_ref, start_date),
        ).fetchone()
        return row[0] if row else None

    def insert_case(
        self, case_id: str, person_ref: str, start_date: date, data: dict[str, Any]
    ) -> None:
        self._conn.execute(
            "INSERT INTO cases (id, person_ref, start_date, data)"
            " VALUES (%s, %s, %s, %s)",
            (case_id, person_ref, start_date, Jsonb(data)),
        )

    def case_data(self, case_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT data FROM cases WHERE id = %s", (case_id,)
        ).fetchone()
        if row is None:
            raise GovernanceError("case_not_found")
        return row[0]

    def merge_case_data(self, case_id: str, values: dict[str, Any]) -> None:
        self._conn.execute(
            "UPDATE cases SET data = data || %s, updated_at = now() WHERE id = %s",
            (Jsonb(values), case_id),
        )

    def lock_case(self, case_id: str) -> CaseRow:
        row = self._conn.execute(
            "SELECT state, current_package_version FROM cases WHERE id = %s FOR UPDATE",
            (case_id,),
        ).fetchone()
        if row is None:
            raise GovernanceError("case_not_found")
        return CaseRow(CaseState(row[0]), row[1])

    def set_state(self, case_id: str, state: CaseState) -> None:
        self._conn.execute(
            "UPDATE cases SET state = %s, updated_at = now() WHERE id = %s",
            (state.value, case_id),
        )

    def add_package_version(
        self, case_id: str, version: int, status: str, lines: list[PackageLine]
    ) -> None:
        self._conn.execute(
            "INSERT INTO package_versions (case_id, version, status)"
            " VALUES (%s, %s, %s)",
            (case_id, version, status),
        )
        with self._conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO package_lines"
                " (case_id, version, field, value, label, source_or_rule_id)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                [
                    (
                        case_id,
                        version,
                        line.field,
                        line.value,
                        line.label,
                        line.source_or_rule_id,
                    )
                    for line in lines
                ],
            )
        self._conn.execute(
            "UPDATE cases SET current_package_version = %s, updated_at = now()"
            " WHERE id = %s",
            (version, case_id),
        )

    def package_status(self, case_id: str, version: int) -> str | None:
        row = self._conn.execute(
            "SELECT status FROM package_versions WHERE case_id = %s AND version = %s",
            (case_id, version),
        ).fetchone()
        return row[0] if row else None

    def add_decision(
        self,
        case_id: str,
        version: int,
        decision: str,
        approval_id: str | None,
        approver_role: str,
        comment: str | None,
    ) -> None:
        self._conn.execute(
            "INSERT INTO approvals"
            " (case_id, package_version, decision, approval_id, approver_role, comment)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (case_id, version, decision, approval_id, approver_role, comment),
        )

    def find_approval(self, approval_id: str) -> Approval | None:
        row = self._conn.execute(
            "SELECT approval_id, case_id, package_version FROM approvals"
            " WHERE approval_id = %s",
            (approval_id,),
        ).fetchone()
        return Approval(*row) if row else None
