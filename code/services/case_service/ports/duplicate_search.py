from datetime import date
from typing import Protocol


class DuplicateSearch(Protocol):
    """The JobDiva READ server's duplicate search: {"found": bool, "start_id": str}."""

    def search_duplicate(self, person_ref: str, start_date: date) -> dict: ...
