"""Access and Equipment agent (Should, S1): US-020 AC-001 and US-021."""

from agents.access_equipment import agent as access
from services.case_service.adapters.rules_files.catalog import RulesCatalog

CATALOG = RulesCatalog.load()
CASE = {"client": "Acme Synthetic", "equipment": "Standard laptop, INSPYR"}


def _line(lines, field):
    return next(line for line in lines if line.field == field)


def test_request_names_provider_and_hardware_tier() -> None:
    # US-020 AC-001
    line = _line(access.recommend(CASE, CATALOG), "equipment_request")

    assert "Chelsea Tech" in line.value
    assert "Standard laptop" in line.value
    assert (line.label, line.source_or_rule_id) == ("recommended", "R-AC-01")


def test_inspyr_equipment_gets_two_percent_overhead() -> None:
    # US-021 AC-001
    line = _line(access.recommend(CASE, CATALOG), "equipment_overhead")

    assert line.value == "2% (INSPYR)"
    assert line.source_or_rule_id == "R-OH-01"


def test_apple_direct_equipment_gets_five_percent_overhead() -> None:
    case = CASE | {"equipment": "MacBook Pro, Apple Direct"}

    line = _line(access.recommend(case, CATALOG), "equipment_overhead")

    assert line.value == "5% (Apple Direct)"
    assert line.source_or_rule_id == "R-OH-02"


def test_client_without_bill_back_rule_is_an_exception() -> None:
    # US-021 AC-002
    case = CASE | {"client": "Beta Synthetic Corp"}

    line = _line(access.recommend(case, CATALOG), "bill_back")

    assert line.label == "exception"
    assert "Onboarding Team" in line.value


def test_client_with_bill_back_rule_cites_it() -> None:
    line = _line(access.recommend(CASE, CATALOG), "bill_back")

    assert (line.label, line.source_or_rule_id) == ("recommended", "R-BB-01")


def test_no_equipment_means_no_request() -> None:
    assert access.recommend({"client": "Acme Synthetic"}, CATALOG) == []


def test_it_request_payload_carries_no_restricted_fields() -> None:
    payload = access.it_request(CASE | {"flsa": "Non-exempt"}, CATALOG)

    assert payload["provider"] == "Chelsea Tech"
    assert payload["hardware"] == "Standard laptop"
    assert "flsa" not in payload
