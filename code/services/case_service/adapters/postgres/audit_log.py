import psycopg
from psycopg.types.json import Jsonb

from ...ports.audit_log import OUTCOMES


class PostgresAuditLog:
    """Appends audit entries on the caller's connection.

    Using the caller's connection keeps an action and its audit entry in the same
    transaction (NFR-REL-002). The caller commits.
    """

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def append(
        self,
        *,
        case_id: str,
        agent: str,
        action: str,
        outcome: str,
        approval_id: str | None = None,
        package_version: int | None = None,
        rule_ids: list[str] | None = None,
        data_refs: dict[str, str] | None = None,
    ) -> None:
        if outcome not in OUTCOMES:
            raise ValueError(
                f"outcome must be one of {sorted(OUTCOMES)}, got {outcome!r}"
            )
        self._conn.execute(
            "INSERT INTO audit_log (case_id, agent, action, outcome, approval_id,"
            " package_version, rule_ids, data_refs)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                case_id,
                agent,
                action,
                outcome,
                approval_id,
                package_version,
                rule_ids or [],
                Jsonb(data_refs or {}),
            ),
        )
