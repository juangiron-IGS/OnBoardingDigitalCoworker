from typing import Literal

from pydantic import BaseModel, Field

Label = Literal["source", "inferred", "recommended", "exception"]
PackageStatus = Literal["ready", "blocked", "needs_clarification"]


class PackageLine(BaseModel):
    """One data point of the approval package (US-011 AC-002)."""

    field: str = Field(min_length=1, max_length=64)
    value: str | None = Field(default=None, max_length=1000)
    label: Label
    source_or_rule_id: str = Field(min_length=1, max_length=128)


def package_status(*, escalated: bool, waiting_answer: bool) -> PackageStatus:
    """US-033: an escalated conflict blocks; an open question needs clarification."""
    if escalated:
        return "blocked"
    if waiting_answer:
        return "needs_clarification"
    return "ready"
