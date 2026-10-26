import psycopg

from .adapters.postgres.audit_log import PostgresAuditLog
from .adapters.postgres.case_repository import PostgresCaseRepository
from .application import decisions
from .application.build_package import build_package
from .application.create_case import CaseIntake, create_case
from .application.move_case import move_case
from .domain.case import CaseState
from .domain.package import PackageLine
from .ports.duplicate_search import DuplicateSearch


class LocalCaseService:
    """In-process implementation of contracts.case_service_api.CaseServiceClient.

    Takes an autocommit connection (see PostgresCaseRepository).
    """

    def __init__(self, conn: psycopg.Connection, jobdiva_read: DuplicateSearch) -> None:
        self._repo = PostgresCaseRepository(conn)
        self._audit = PostgresAuditLog(conn)
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

    def case_state(self, case_id: str) -> CaseState:
        return self._repo.lock_case(case_id).state

    def current_package_version(self, case_id: str) -> int:
        return self._repo.lock_case(case_id).current_package_version
