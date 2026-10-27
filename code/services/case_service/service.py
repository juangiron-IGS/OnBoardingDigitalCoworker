from typing import Any

import psycopg

from .adapters.postgres import queries
from .adapters.postgres.audit_log import PostgresAuditLog
from .adapters.postgres.case_repository import PostgresCaseRepository
from .adapters.postgres.followup_repository import PostgresFollowupRepository
from .application import decisions, followup
from .application.assign_owner import assign_owner
from .application.build_package import build_package
from .application.case_data import log_action, record_answers
from .application.create_case import CaseIntake, create_case
from .application.it_approval import record_it_approval
from .application.move_case import move_case
from .domain.case import CaseState
from .domain.package import PackageLine
from .domain.privacy import HIDDEN, RESTRICTED_FIELDS, can_see_restricted, redact
from .ports.duplicate_search import DuplicateSearch


class LocalCaseService:
    """In-process implementation of contracts.case_service_api.CaseServiceClient.

    Takes an autocommit connection (see PostgresCaseRepository).
    """

    def __init__(self, conn: psycopg.Connection, jobdiva_read: DuplicateSearch) -> None:
        self._conn = conn
        self._repo = PostgresCaseRepository(conn)
        self._audit = PostgresAuditLog(conn)
        self._followup = PostgresFollowupRepository(conn)
        self._jobdiva_read = jobdiva_read

    def create_case(self, intake: CaseIntake, *, agent: str) -> str:
        return create_case(
            self._repo, self._audit, self._jobdiva_read, intake, agent=agent
        )

    def move_case(self, case_id: str, target: CaseState, *, agent: str) -> CaseState:
        return move_case(self._repo, self._audit, case_id, target, agent=agent)

    def build_package(
        self,
        case_id: str,
        lines: list[PackageLine],
        *,
        agent: str,
        escalated: bool = False,
        waiting_answer: bool = False,
    ) -> int:
        return build_package(
            self._repo,
            self._audit,
            case_id,
            lines,
            agent=agent,
            escalated=escalated,
            waiting_answer=waiting_answer,
        )

    def record_approval(
        self,
        case_id: str,
        *,
        package_version: int,
        approver_role: str,
        comment: str | None = None,
    ) -> str:
        return decisions.record_approval(
            self._repo,
            self._audit,
            case_id=case_id,
            package_version=package_version,
            approver_role=approver_role,
            comment=comment,
        )

    def return_package(
        self,
        case_id: str,
        *,
        package_version: int,
        approver_role: str,
        comment: str | None = None,
    ) -> None:
        decisions.return_package(
            self._repo,
            self._audit,
            case_id=case_id,
            package_version=package_version,
            approver_role=approver_role,
            comment=comment,
        )

    def reject_case(
        self,
        case_id: str,
        *,
        package_version: int,
        approver_role: str,
        comment: str | None = None,
    ) -> None:
        decisions.reject_case(
            self._repo,
            self._audit,
            case_id=case_id,
            package_version=package_version,
            approver_role=approver_role,
            comment=comment,
        )

    def assign_owner(self, case_id: str, owner: str, *, assigned_by: str) -> None:
        assign_owner(self._repo, self._audit, case_id, owner, assigned_by=assigned_by)

    def record_it_approval(
        self, case_id: str, *, package_version: int, approver_role: str
    ) -> None:
        record_it_approval(
            self._repo,
            self._audit,
            case_id,
            package_version=package_version,
            approver_role=approver_role,
        )

    def it_approved(self, case_id: str, package_version: int) -> bool:
        return self._repo.it_approved(case_id, package_version)

    def has_it_request(self, case_id: str, package_version: int) -> bool:
        return self._repo.has_line(case_id, package_version, "equipment_request")

    def approval_id_for(self, case_id: str, package_version: int) -> str | None:
        return self._repo.approval_id_for(case_id, package_version)

    def case_state(self, case_id: str) -> CaseState:
        return self._repo.lock_case(case_id).state

    def current_package_version(self, case_id: str) -> int:
        return self._repo.lock_case(case_id).current_package_version

    def case_data(self, case_id: str) -> dict[str, Any]:
        return self._repo.case_data(case_id)

    def record_answers(
        self, case_id: str, values: dict[str, Any], *, agent: str, source: str
    ) -> None:
        record_answers(
            self._repo, self._audit, case_id, values, agent=agent, source=source
        )

    def log_action(
        self,
        case_id: str,
        *,
        agent: str,
        action: str,
        outcome: str = "completed",
        rule_ids: list[str] | None = None,
        data_refs: dict[str, str] | None = None,
    ) -> None:
        log_action(
            self._repo,
            self._audit,
            case_id,
            agent=agent,
            action=action,
            outcome=outcome,
            rule_ids=rule_ids,
            data_refs=data_refs,
        )

    def package_lines(self, case_id: str, package_version: int) -> list[dict]:
        package = queries.package(self._conn, case_id, package_version)
        return package["lines"] if package else []

    # After approval: checklist, reminders, document check, payroll (US-022..024)
    def send_checklist(
        self, case_id: str, items: list[tuple[str, str]], *, agent: str
    ) -> None:
        followup.send_checklist(
            self._repo, self._followup, self._audit, case_id, items, agent=agent
        )

    def checklist(self, case_id: str) -> list[dict[str, Any]]:
        return self._followup.checklist(case_id)

    def reminders(self, case_id: str) -> list[dict[str, Any]]:
        return self._followup.reminders(case_id)

    def record_reminder(
        self, case_id: str, *, kind: str, at_hours: int, rule_id: str, agent: str
    ) -> None:
        followup.record_reminder(
            self._repo,
            self._followup,
            self._audit,
            case_id,
            kind=kind,
            at_hours=at_hours,
            rule_id=rule_id,
            agent=agent,
        )

    def record_delivery(
        self, case_id: str, items: list[str], *, recorded_by: str
    ) -> list[str]:
        return followup.record_delivery(
            self._repo,
            self._followup,
            self._audit,
            case_id,
            items,
            recorded_by=recorded_by,
        )

    def countersign(self, case_id: str, item: str, *, signed_by: str) -> None:
        followup.countersign(
            self._repo, self._followup, self._audit, case_id, item, signed_by=signed_by
        )

    def approve_payroll_handoff(
        self, case_id: str, *, package_version: int, approved_by: str
    ) -> None:
        followup.approve_payroll_handoff(
            self._repo,
            self._followup,
            self._audit,
            case_id,
            package_version=package_version,
            approved_by=approved_by,
        )

    def record_payroll_return(self, case_id: str, issue: str, *, agent: str) -> int:
        return followup.record_payroll_return(
            self._repo, self._followup, self._audit, case_id, issue, agent=agent
        )

    def payroll_returns(self, case_id: str) -> list[dict[str, Any]]:
        return self._followup.payroll_returns(case_id)

    def find_case(self, ref: str) -> str | None:
        return queries.find_case(self._conn, ref)

    def list_cases(self) -> list[dict[str, Any]]:
        return queries.list_cases(self._conn)

    def case_view(self, case_id: str, *, role: str) -> dict[str, Any] | None:
        """The case as this role may see it: restricted values hidden (US-040)."""
        view = queries.case_detail(self._conn, case_id)
        if view is None:
            return None
        view["case"]["data"] = redact(view["case"]["data"], role)
        if view["package"] and not can_see_restricted(role):
            for line in view["package"]["lines"]:
                if line["field"] in RESTRICTED_FIELDS:
                    line["value"] = HIDDEN
        for record in view["records"]:  # the payroll package carries FLSA
            record["data"] = redact(record["data"], role)
        view["checklist"] = self._followup.checklist(case_id)
        view["reminders"] = self._followup.reminders(case_id)
        view["payroll_returns"] = self._followup.payroll_returns(case_id)
        return view
