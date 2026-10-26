from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

from ..domain.approval_gate import Approval
from ..domain.case import CaseState
from ..domain.package import PackageLine


@dataclass(frozen=True)
class CaseRow:
    state: CaseState
    current_package_version: int


class CaseRepository(Protocol):
    def transaction(self) -> AbstractContextManager[Any]: ...

    def find_case_id(self, person_ref: str, start_date: date) -> str | None: ...

    def insert_case(
        self, case_id: str, person_ref: str, start_date: date, data: dict[str, Any]
    ) -> None: ...

    def case_data(self, case_id: str) -> dict[str, Any]: ...

    def merge_case_data(self, case_id: str, values: dict[str, Any]) -> None: ...

    def lock_case(self, case_id: str) -> CaseRow:
        """Read the case and lock it until the transaction ends."""
        ...

    def set_state(self, case_id: str, state: CaseState) -> None: ...

    def add_package_version(
        self, case_id: str, version: int, status: str, lines: list[PackageLine]
    ) -> None:
        """Store a new version with its lines and make it the current one."""
        ...

    def package_status(self, case_id: str, version: int) -> str | None: ...

    def add_decision(
        self,
        case_id: str,
        version: int,
        decision: str,
        approval_id: str | None,
        approver_role: str,
        comment: str | None,
    ) -> None: ...

    def find_approval(self, approval_id: str) -> Approval | None: ...
