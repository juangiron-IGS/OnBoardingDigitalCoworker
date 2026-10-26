from dataclasses import dataclass

from .errors import ApprovalRefused


@dataclass(frozen=True)
class Approval:
    approval_id: str
    case_id: str
    package_version: int


def verify(approval: Approval | None, current_package_version: int) -> None:
    """Raise ApprovalRefused unless the approval is for the current version.

    BR-002.
    """
    if approval is None:
        raise ApprovalRefused("no_approval")
    if approval.package_version != current_package_version:
        raise ApprovalRefused("version_mismatch")
