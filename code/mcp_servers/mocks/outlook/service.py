from email import policy
from email.message import EmailMessage
from email.parser import Parser
from pathlib import Path

import psycopg

SEED_MAILBOX = Path(__file__).resolve().parents[3] / "db" / "seed" / "mailbox"
DELIVERED = "mail-"


class MailboxService:
    """The onboarding mailbox mock: synthetic start emails.

    Implements contracts.mcp_tools.Mailbox. The seed emails are .eml files whose ID
    is the file name without its extension; emails that arrive during a demo are
    kept in mocks.inbound_mail with IDs "mail-<n>". Only listed IDs can be read.
    """

    def __init__(
        self, folder: Path = SEED_MAILBOX, conn: psycopg.Connection | None = None
    ) -> None:
        self._folder = folder
        self._conn = conn

    def list_messages(self) -> list[dict]:
        seed = [self._headers(path) for path in sorted(self._folder.glob("*.eml"))]
        return self._delivered() + seed

    def read_message(self, message_id: str) -> dict:
        if message_id.startswith(DELIVERED) and self._conn is not None:
            return self._read_delivered(message_id)
        paths = {path.stem: path for path in self._folder.glob("*.eml")}
        if message_id not in paths:
            raise KeyError(message_id)
        message = self._parse(paths[message_id])
        return {**self._headers(paths[message_id]), "body": message.get_content()}

    def deliver(self, sender: str, subject: str, body: str) -> str:
        """A new email arrives in the onboarding mailbox."""
        row = (
            self._db()
            .execute(
                "INSERT INTO mocks.inbound_mail (sender, subject, body)"
                " VALUES (%s, %s, %s) RETURNING id",
                (sender, subject, body),
            )
            .fetchone()
        )
        return f"{DELIVERED}{row[0]}"

    def record_outcome(
        self, message_id: str, case_id: str | None, outcome: str
    ) -> None:
        self._db().execute(
            "UPDATE mocks.inbound_mail SET case_id = %s, outcome = %s WHERE id = %s",
            (case_id, outcome, self._number(message_id)),
        )

    def _delivered(self) -> list[dict]:
        if self._conn is None:
            return []
        rows = self._conn.execute(
            "SELECT id, sender, subject, received_at, case_id, outcome"
            " FROM mocks.inbound_mail ORDER BY id DESC LIMIT 100"
        ).fetchall()
        return [
            {
                "id": f"{DELIVERED}{r[0]}",
                "from": r[1],
                "subject": r[2],
                "received_at": r[3].isoformat(),
                "case_id": r[4],
                "outcome": r[5],
            }
            for r in rows
        ]

    def _read_delivered(self, message_id: str) -> dict:
        row = (
            self._db()
            .execute(
                "SELECT sender, subject, body FROM mocks.inbound_mail WHERE id = %s",
                (self._number(message_id),),
            )
            .fetchone()
        )
        if row is None:
            raise KeyError(message_id)
        return {"id": message_id, "from": row[0], "subject": row[1], "body": row[2]}

    def _db(self) -> psycopg.Connection:
        if self._conn is None:
            raise RuntimeError("delivering email needs a database connection")
        return self._conn

    @staticmethod
    def _number(message_id: str) -> int:
        try:
            return int(message_id.removeprefix(DELIVERED))
        except ValueError:
            raise KeyError(message_id) from None

    def _headers(self, path: Path) -> dict:
        message = self._parse(path)
        return {"id": path.stem, "from": message["From"], "subject": message["Subject"]}

    @staticmethod
    def _parse(path: Path) -> EmailMessage:
        return Parser(policy=policy.default).parsestr(path.read_text(encoding="utf-8"))
