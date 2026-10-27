"""The case service operations shared by lane A (governance) and lane B (agents, web).

Agents and the web API call the case service only through this interface.
Changing this file needs an approval from someone in each lane.
"""

from typing import Any, Protocol, runtime_checkable

from services.case_service.application.create_case import CaseIntake
from services.case_service.domain.case import CaseState
from services.case_service.domain.package import PackageLine

__all__ = ["CaseIntake", "CaseServiceClient", "CaseState", "PackageLine"]


@runtime_checkable
class CaseServiceClient(Protocol):
    def create_case(self, intake: CaseIntake, *, agent: str) -> str:
        """Create a case in Received. Raises DuplicateCase (BR-004)."""
        ...

    def move_case(self, case_id: str, target: CaseState, *, agent: str) -> CaseState:
        """Raises InvalidTransition for a move the case states do not allow."""
        ...

    def build_package(
        self,
        case_id: str,
        lines: list[PackageLine],
        *,
        agent: str,
        escalated: bool = False,
        waiting_answer: bool = False,
    ) -> int:
        """Store a new package version for a case in Case set up; return it."""
        ...

    def record_approval(
        self,
        case_id: str,
        *,
        package_version: int,
        approver_role: str,
        comment: str | None = None,
    ) -> str:
        """Approve the current version and return the approval ID (BR-002)."""
        ...

    def return_package(
        self,
        case_id: str,
        *,
        package_version: int,
        approver_role: str,
        comment: str | None = None,
    ) -> None: ...

    def reject_case(
        self,
        case_id: str,
        *,
        package_version: int,
        approver_role: str,
        comment: str | None = None,
    ) -> None: ...

    def case_state(self, case_id: str) -> CaseState: ...

    def current_package_version(self, case_id: str) -> int: ...

    def case_data(self, case_id: str) -> dict[str, Any]: ...

    def record_it_approval(
        self, case_id: str, *, package_version: int, approver_role: str
    ) -> None:
        """IT approves the access and laptop request of this version (BR-012)."""
        ...

    def it_approved(self, case_id: str, package_version: int) -> bool: ...

    def has_it_request(self, case_id: str, package_version: int) -> bool: ...

    def approval_id_for(self, case_id: str, package_version: int) -> str | None:
        """The approval ID of this version, or None if it is not approved."""
        ...

    def assign_owner(self, case_id: str, owner: str, *, assigned_by: str) -> None:
        """A person assigns the follow-up owner (US-032); the audit records who."""
        ...

    def find_case(self, ref: str) -> str | None:
        """A case by its ID or candidate reference, or None."""
        ...

    def record_answers(
        self, case_id: str, values: dict[str, Any], *, agent: str, source: str
    ) -> None:
        """Merge confirmed values into the case; the audit names fields only."""
        ...

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
        """Audit an agent action that changes no case data (US-018)."""
        ...
