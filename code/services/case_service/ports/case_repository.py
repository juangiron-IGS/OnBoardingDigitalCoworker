from contextlib import AbstractContextManager
from datetime import date
from typing import Any, Protocol


class CaseRepository(Protocol):
    def transaction(self) -> AbstractContextManager[Any]: ...

    def find_case_id(self, person_ref: str, start_date: date) -> str | None: ...

    def insert_case(
        self, case_id: str, person_ref: str, start_date: date, data: dict[str, Any]
    ) -> None: ...
