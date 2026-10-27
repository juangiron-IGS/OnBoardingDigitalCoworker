from datetime import date

from agents.orchestrator.dashboard import _risks
from contracts.case_service_api import CaseState


def _view(start: str, status: str = "ready") -> dict:
    return {
        "case": {"start_date": start, "package_timing": {"met": False}},
        "package": {"status": status, "lines": []},
        "reminders": [{"kind": "escalation"}],
    }


def test_risks_name_a_close_start_and_a_missed_target() -> None:
    risks = _risks(
        _view("2026-11-01"), CaseState.READY_FOR_REVIEW, today=date(2026, 10, 28)
    )

    assert risks == [
        "Starts in 4 day(s), not approved",
        "Package missed the 5-minute target",
    ]


def test_escalated_documents_are_a_risk_while_they_are_pending() -> None:
    pending = _risks(
        _view("2026-12-01"), CaseState.DOCUMENTS_PENDING, today=date(2026, 10, 28)
    )
    sent = _risks(
        _view("2026-12-01"), CaseState.SENT_TO_PAYROLL, today=date(2026, 10, 28)
    )

    assert "Documents escalated after the reminders" in pending
    assert "Documents escalated after the reminders" not in sent


def test_an_approved_case_is_not_at_risk_for_its_start_date() -> None:
    risks = _risks(
        _view("2026-11-01"), CaseState.ACTIONS_EXECUTED, today=date(2026, 10, 28)
    )

    assert not any(r.startswith("Starts") for r in risks)
