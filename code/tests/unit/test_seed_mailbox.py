from pathlib import Path

import pytest

from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter

MAILBOX = Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"

MANDATORY = [
    "work_city", "work_state", "flsa", "billing_contact", "timesheet_approver",
    "equipment", "sponsorship_visa", "person_ref", "role", "manager", "start_date",
    "client", "division", "line_of_business", "employment_type", "vendor_company",
    "work_arrangement", "pay_rate", "bill_rate",
]  # fmt: skip


def _read(name: str):
    client = RulesModelClient(load_labels(), UsageMeter(cap_per_run=100))
    text = (MAILBOX / name).read_text(encoding="utf-8")
    return client.extract_fields(text, MANDATORY, case_id="seed", run_id="seed")


def test_complete_scenario_has_every_mandatory_field() -> None:
    result = _read("01_complete_and_consistent.eml")

    assert [f for f, v in result.values.items() if v is None] == []
    assert result.ambiguous == []


def test_demo_scenario_misses_exactly_two_fields() -> None:
    # Checkpoint demo: "2 fields missing"
    result = _read("02_missing_two_fields.eml")

    missing = sorted(f for f, v in result.values.items() if v is None)
    assert missing == ["bill_rate", "timesheet_approver"]


def test_duplicate_scenario_repeats_person_and_start_date() -> None:
    first = _read("01_complete_and_consistent.eml").values
    duplicate = _read("03_duplicate.eml").values

    assert (duplicate["person_ref"], duplicate["start_date"]) == (
        first["person_ref"],
        first["start_date"],
    )


def test_contradiction_scenario_flags_work_arrangement() -> None:
    assert _read("04_work_arrangement_contradiction.eml").ambiguous == [
        "work_arrangement"
    ]


@pytest.mark.parametrize("path", sorted(MAILBOX.glob("*.eml")), ids=lambda p: p.name)
def test_every_seed_email_is_synthetic(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    assert "SYN-" in text
    assert "@example.com" in text or "@example.org" in text
