from contextlib import AbstractContextManager
from datetime import date
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


class PostgresCaseRepository:
    """Case store on the caller's connection, so writes share its transaction."""

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
