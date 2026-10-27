from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from contracts.mcp_tools import SIMULATED_ACTIONS, idempotency_key
from services.case_service.adapters.postgres.audit_log import PostgresAuditLog
from services.case_service.adapters.postgres.case_repository import (
    PostgresCaseRepository,
)
from services.case_service.adapters.postgres.followup_repository import (
    PostgresFollowupRepository,
)
from services.case_service.application.decisions import authorize_action
from services.case_service.domain.errors import ApprovalRefused, GovernanceError

AGENT = "jobdiva_workflow"

# Each simulated action writes one row to its mock store.
_STORES = {
    "create_jobdiva_case": "jobdiva_cases",
    "create_task_list": "task_lists",
    "create_it_request": "it_requests",
    "send_payroll_package": "payroll_packages",
}
if frozenset(_STORES) != SIMULATED_ACTIONS:
    raise RuntimeError("Every simulated action needs exactly one mock store")


class WorkflowService:
    """The single writer (BR-002, US-034): applies approved actions to mock stores.

    Implements contracts.mcp_tools.JobDivaWorkflow on an autocommit connection.
    """

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn
        self._repo = PostgresCaseRepository(conn)
        self._audit = PostgresAuditLog(conn)
        self._followup = PostgresFollowupRepository(conn)

    def execute_simulated_action(
        self,
        approval_id: str,
        package_version: int,
        action: str,
        payload: dict[str, Any],
    ) -> dict:
        key = idempotency_key(approval_id, action)
        case_id = "unknown"
        try:
            if action not in SIMULATED_ACTIONS:
                raise GovernanceError("unknown_action")
            with self._repo.transaction():
                if self._already_applied(key):
                    return {"status": "already_completed", "key": key}
                # Re-verify against the database inside this transaction: the case
                # stays locked until the action and its audit entry commit.
                approval = authorize_action(self._repo, approval_id=approval_id)
                case_id = approval.case_id
                if approval.package_version != package_version:
                    raise ApprovalRefused("version_mismatch")
                if action == "create_it_request" and not self._repo.it_approved(
                    case_id, package_version
                ):
                    raise GovernanceError("it_not_approved")  # BR-012, US-020 AC-002
                if action == "send_payroll_package" and not (
                    self._followup.payroll_handoff_approved(case_id, package_version)
                ):
                    raise GovernanceError("handoff_not_approved")  # US-024 AC-002
                self._apply(action, case_id, approval_id, payload)
                self._conn.execute(
                    "INSERT INTO action_ledger"
                    " (idempotency_key, approval_id, package_version, action)"
                    " VALUES (%s, %s, %s, %s)",
                    (key, approval_id, package_version, action),
                )
                self._audit.append(
                    case_id=case_id,
                    agent=AGENT,
                    action=action,
                    outcome="completed",
                    approval_id=approval_id,
                    package_version=package_version,
                    data_refs={field: "package" for field in payload},
                )
            return {"status": "completed", "key": key}
        except GovernanceError:
            # Its own transaction, so the refusal is kept when the action is not.
            with self._repo.transaction():
                self._audit.append(
                    case_id=case_id,
                    agent=AGENT,
                    action=action,
                    outcome="refused",
                    approval_id=approval_id,
                    package_version=package_version,
                )
            raise

    def _already_applied(self, key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM action_ledger WHERE idempotency_key = %s", (key,)
        ).fetchone()
        return row is not None

    def _apply(
        self, action: str, case_id: str, approval_id: str, payload: dict[str, Any]
    ) -> None:
        self._conn.execute(
            sql.SQL(
                "INSERT INTO mocks.{} (case_id, approval_id, data) VALUES (%s, %s, %s)"
            ).format(sql.Identifier(_STORES[action])),
            (case_id, approval_id, Jsonb(payload)),
        )
