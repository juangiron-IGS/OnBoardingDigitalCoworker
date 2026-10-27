from datetime import datetime
from typing import Any

import psycopg


class PostgresFollowupRepository:
    """Checklist, reminders, payroll handoff and returns on the caller's connection,
    so each write shares the transaction of its audit entry (NFR-REL-002)."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def add_items(self, case_id: str, items: list[tuple[str, str]]) -> None:
        for item, required_by in items:
            self._conn.execute(
                "INSERT INTO document_checklist (case_id, item, required_by)"
                " VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (case_id, item, required_by),
            )

    def checklist(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT item, required_by, status, sent_at, delivered_at, verified_by,"
            " verified_at FROM document_checklist WHERE case_id = %s ORDER BY id",
            (case_id,),
        ).fetchall()
        return [
            {
                "item": r[0],
                "required_by": r[1],
                "status": r[2],
                "sent_at": _iso(r[3]),
                "delivered_at": _iso(r[4]),
                "verified_by": r[5],
                "verified_at": _iso(r[6]),
            }
            for r in rows
        ]

    def set_status(
        self, case_id: str, item: str, status: str, *, verified_by: str | None = None
    ) -> None:
        if status == "pending_countersign":
            self._conn.execute(
                "UPDATE document_checklist SET status = %s, delivered_at = now()"
                " WHERE case_id = %s AND item = %s",
                (status, case_id, item),
            )
        else:
            self._conn.execute(
                "UPDATE document_checklist SET status = %s, verified_by = %s,"
                " verified_at = now() WHERE case_id = %s AND item = %s",
                (status, verified_by, case_id, item),
            )

    def add_reminder(
        self, case_id: str, kind: str, at_hours: int, rule_id: str
    ) -> None:
        self._conn.execute(
            "INSERT INTO followup_reminders (case_id, kind, at_hours, rule_id)"
            " VALUES (%s, %s, %s, %s)",
            (case_id, kind, at_hours, rule_id),
        )

    def reminders(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT kind, at_hours, rule_id, sent_at FROM followup_reminders"
            " WHERE case_id = %s ORDER BY id",
            (case_id,),
        ).fetchall()
        return [
            {"kind": r[0], "at_hours": r[1], "rule_id": r[2], "sent_at": _iso(r[3])}
            for r in rows
        ]

    def add_payroll_handoff(self, case_id: str, version: int, approved_by: str) -> None:
        self._conn.execute(
            "INSERT INTO payroll_handoffs (case_id, package_version, approved_by)"
            " VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (case_id, version, approved_by),
        )

    def payroll_handoff_approved(self, case_id: str, version: int) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM payroll_handoffs"
            " WHERE case_id = %s AND package_version = %s",
            (case_id, version),
        ).fetchone()
        return row is not None

    def add_payroll_return(self, case_id: str, issue: str) -> int:
        return self._conn.execute(
            "INSERT INTO payroll_returns (case_id, issue) VALUES (%s, %s) RETURNING id",
            (case_id, issue),
        ).fetchone()[0]

    def payroll_returns(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, issue, received_at FROM payroll_returns"
            " WHERE case_id = %s ORDER BY id",
            (case_id,),
        ).fetchall()
        return [{"id": r[0], "issue": r[1], "received_at": _iso(r[2])} for r in rows]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
