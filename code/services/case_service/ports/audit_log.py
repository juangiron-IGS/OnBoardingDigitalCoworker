from typing import Protocol

OUTCOMES = frozenset({"completed", "refused", "failed"})


class AuditLog(Protocol):
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
    ) -> None: ...

    # data_refs maps field names to their source. Restricted fields appear by name,
    # never by value.
