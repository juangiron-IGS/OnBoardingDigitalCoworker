import psycopg

from . import webhook


class AlertsService:
    """The Teams mock: alerts go to the simulated alerts view (TC-005, no bot).

    Implements contracts.mcp_tools.Alerts on an autocommit connection.
    """

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def post_alert(self, case_id: str, recipient: str, text: str) -> dict:
        row = self._conn.execute(
            "INSERT INTO mocks.alerts (case_id, recipient, text) VALUES (%s, %s, %s)"
            " RETURNING id",
            (case_id, recipient, text),
        ).fetchone()
        webhook.mirror(recipient, text)  # optional copy to a real channel
        return {"id": row[0], "status": "posted"}

    def list_alerts(self, case_id: str | None = None) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, case_id, recipient, text, created_at FROM mocks.alerts"
            " WHERE %(case)s::text IS NULL OR case_id = %(case)s ORDER BY id DESC",
            {"case": case_id},
        ).fetchall()
        return [
            {
                "id": r[0],
                "case_id": r[1],
                "recipient": r[2],
                "text": r[3],
                "at": r[4].isoformat(),
            }
            for r in rows
        ]
