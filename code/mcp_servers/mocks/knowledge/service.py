from datetime import date
from pathlib import Path
from typing import Literal

import psycopg
import yaml
from pydantic import BaseModel, Field

from services.case_service.adapters.postgres.audit_log import PostgresAuditLog

RULES = Path(__file__).resolve().parents[3] / "rules"
RECORDS_FILE = RULES / "knowledge" / "records.yaml"
AUDIT_CASE = "knowledge"  # audit entries that belong to no onboarding case
PENDING = "Q-"


class Record(BaseModel):
    """Checkpoint data model "Knowledge record"."""

    id: str = Field(pattern=r"^KB-\d{3}$")
    type: Literal["question", "solution", "procedure"]
    title: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=300)
    answer: str = Field(min_length=1, max_length=2000)
    steps: list[str] = Field(default_factory=list, max_length=20)
    category: str = Field(min_length=1, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=20)
    status: Literal["validated", "unvalidated"]
    source: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=60)
    date: date


def load_records(path: Path = RECORDS_FILE) -> list[Record]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Record(**entry) for entry in doc.get("records", [])]


class KnowledgeService:
    """The knowledge base mock (checkpoint "Onboarding knowledge module").

    Records are data the business maintains in rules/knowledge. The Onboarding
    Team's validation decisions and the questions no record answers live in
    mocks.knowledge_*; the latest decision on a record sets its status. Every
    change is audited on the same connection.
    """

    def __init__(
        self, conn: psycopg.Connection, records: list[Record] | None = None
    ) -> None:
        self._conn = conn
        self._records = load_records() if records is None else records
        self._audit = PostgresAuditLog(conn)

    def records(self) -> list[dict]:
        """searchKnowledge: every record with its current status."""
        decisions = dict(
            self._conn.execute(
                "SELECT DISTINCT ON (record_id) record_id, decision"
                " FROM mocks.knowledge_validations ORDER BY record_id, id DESC"
            ).fetchall()
        )
        return [
            {**r.model_dump(mode="json"), "status": decisions.get(r.id, r.status)}
            for r in self._records
        ]

    def validate(self, record_id: str, decision: str, *, decided_by: str) -> str:
        """validateKnowledge: the Onboarding Team validates or rejects a record."""
        if record_id not in {r.id for r in self._records}:
            raise KeyError(record_id)
        if decision not in ("validated", "rejected"):
            raise ValueError("decision must be validated or rejected")
        with self._conn.transaction():  # the decision and its audit entry together
            self._conn.execute(
                "INSERT INTO mocks.knowledge_validations"
                " (record_id, decision, decided_by) VALUES (%s, %s, %s)",
                (record_id, decision, decided_by),
            )
            self._audit.append(
                case_id=AUDIT_CASE,
                agent=decided_by,
                action=f"knowledge_{decision}",
                outcome="completed",
                rule_ids=[record_id],
            )
        return decision

    def register_unresolved(
        self, question: str, *, asked_by: str, channel: str, reason: str
    ) -> str:
        """registerUnresolved: keep a question pending for the Onboarding Team."""
        with self._conn.transaction():
            row = self._conn.execute(
                "INSERT INTO mocks.knowledge_questions"
                " (question, asked_by, channel, reason)"
                " VALUES (%s, %s, %s, %s) RETURNING id",
                (question, asked_by, channel, reason),
            ).fetchone()
            pending_id = f"{PENDING}{row[0]}"
            self._audit.append(
                case_id=AUDIT_CASE,
                agent="onboarding_knowledge",
                action="register_unresolved",
                outcome="completed",
                data_refs={"question": channel, "pending_id": pending_id},
            )
        return pending_id

    def log_answer(self, record_id: str, status: str, *, channel: str) -> None:
        self._audit.append(
            case_id=AUDIT_CASE,
            agent="onboarding_knowledge",
            action="answer_from_knowledge",
            outcome="completed",
            rule_ids=[record_id],
            data_refs={"question": channel, "record_status": status},
        )

    def pending(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, question, asked_by, channel, reason, asked_at"
            " FROM mocks.knowledge_questions ORDER BY id DESC LIMIT 100"
        ).fetchall()
        return [
            {
                "id": f"{PENDING}{r[0]}",
                "question": r[1],
                "asked_by": r[2],
                "channel": r[3],
                "reason": r[4],
                "asked_at": r[5].isoformat(),
            }
            for r in rows
        ]
