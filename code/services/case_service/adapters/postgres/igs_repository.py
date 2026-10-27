from typing import Any

import psycopg


class PostgresIgsRepository:
    """LDC kit approvals and leader messages on the caller's connection, so each
    write shares the transaction of its audit entry (NFR-REL-002)."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def add_kit_approval(self, case_id: str, version: int, approved_by: str) -> None:
        self._conn.execute(
            "INSERT INTO ldc_kit_approvals (case_id, package_version, approved_by)"
            " VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (case_id, version, approved_by),
        )

    def kit_approved(self, case_id: str, version: int) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM ldc_kit_approvals"
            " WHERE case_id = %s AND package_version = %s",
            (case_id, version),
        ).fetchone()
        return row is not None

    def add_message(
        self, case_id: str, kind: str, recipient: str, text: str, rule_id: str
    ) -> None:
        self._conn.execute(
            "INSERT INTO leader_messages (case_id, kind, recipient, text, rule_id)"
            " VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (case_id, kind, recipient, text, rule_id),
        )

    def messages(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, kind, recipient, text, rule_id, status, approved_by, sent_at"
            " FROM leader_messages WHERE case_id = %s ORDER BY id",
            (case_id,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "kind": r[1],
                "recipient": r[2],
                "text": r[3],
                "rule_id": r[4],
                "status": r[5],
                "approved_by": r[6],
                "sent_at": r[7].isoformat() if r[7] else None,
            }
            for r in rows
        ]

    def message(self, case_id: str, message_id: int) -> dict[str, Any] | None:
        return next((m for m in self.messages(case_id) if m["id"] == message_id), None)

    def set_message_status(
        self, message_id: int, status: str, *, approved_by: str | None = None
    ) -> None:
        if status == "approved":
            self._conn.execute(
                "UPDATE leader_messages SET status = %s, approved_by = %s"
                " WHERE id = %s",
                (status, approved_by, message_id),
            )
        else:
            self._conn.execute(
                "UPDATE leader_messages SET status = %s, sent_at = now() WHERE id = %s",
                (status, message_id),
            )
