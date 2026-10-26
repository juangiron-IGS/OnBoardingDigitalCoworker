import pytest
from pydantic import ValidationError

from services.case_service.domain.approval_gate import Approval, verify
from services.case_service.domain.errors import ApprovalRefused
from services.case_service.domain.package import PackageLine, package_status


def test_package_line_requires_label_and_source() -> None:
    # US-011 AC-002: every data point carries a label and its source or rule ID
    line = PackageLine(
        field="paperwork",
        value="CA-DE4",
        label="recommended",
        source_or_rule_id="R-PA-02",
    )
    assert line.label == "recommended"

    with pytest.raises(ValidationError):
        PackageLine(field="x", value="y", label="guess", source_or_rule_id="R-1")
    with pytest.raises(ValidationError):
        PackageLine(field="x", value="y", label="source", source_or_rule_id="")


def test_package_status_blocked_when_escalated() -> None:
    # US-033 AC-001: an escalated FLSA conflict blocks the package
    assert package_status(escalated=True, waiting_answer=True) == "blocked"


def test_package_status_needs_clarification_when_waiting() -> None:
    # US-033 AC-002
    assert package_status(escalated=False, waiting_answer=True) == (
        "needs_clarification"
    )


def test_package_status_ready() -> None:
    assert package_status(escalated=False, waiting_answer=False) == "ready"


def test_verify_refuses_missing_approval() -> None:
    with pytest.raises(ApprovalRefused) as refusal:
        verify(None, current_package_version=1)
    assert refusal.value.reason == "no_approval"


def test_verify_refuses_other_version() -> None:
    # US-015 AC-003
    with pytest.raises(ApprovalRefused) as refusal:
        verify(Approval("apr-1", "case-1", 2), current_package_version=3)
    assert refusal.value.reason == "version_mismatch"


def test_verify_accepts_current_version() -> None:
    verify(Approval("apr-1", "case-1", 3), current_package_version=3)
