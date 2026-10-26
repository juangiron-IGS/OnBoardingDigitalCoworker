"""The case service operations shared by lane A (governance) and lane B (agents, web).

Agents and the web API call the case service only through this interface.
Changing this file needs an approval from someone in each lane.
"""

from typing import Protocol, runtime_checkable

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
