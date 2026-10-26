import pytest

from services.case_service.adapters.rules_files.catalog import (
    RULES_ROOT,
    RulesCatalog,
)

CA_W2 = {
    "employment_type": "W-2",
    "flsa": "Non-exempt",
    "work_state": "CA",
    "work_city": "San Diego",
    "client": "Acme Synthetic",
}


@pytest.fixture(scope="module")
def catalog() -> RulesCatalog:
    return RulesCatalog.load(RULES_ROOT)


def test_lookup_returns_rule_with_its_id(catalog) -> None:
    # US-007 AC-002: each form is listed with the rule that required it
    rules = catalog.matching("paperwork", CA_W2)

    assert rules
    assert all(rule.id in catalog.ids() for rule in rules)
    assert "CA state withholding form (DE 4)" in {r.result["form"] for r in rules}


def test_rule_shows_owner_and_version(catalog) -> None:
    # US-007 AC-003
    rule = catalog.get("R-PA-02")

    assert rule.owner in {"Onboarding", "IT", "LDC"}
    assert rule.version >= 1


def test_texas_has_no_state_forms(catalog) -> None:
    tx = {**CA_W2, "work_state": "TX", "work_city": "Austin"}

    forms = {r.result["form"] for r in catalog.matching("paperwork", tx)}

    assert not any("CA" in form or "Philadelphia" in form for form in forms)
    assert "Federal withholding form (W-4)" in forms


def test_philadelphia_adds_the_city_form(catalog) -> None:
    pa = {**CA_W2, "work_state": "PA", "work_city": "Philadelphia"}

    forms = {r.result["form"] for r in catalog.matching("paperwork", pa)}

    assert "Philadelphia city wage tax notice" in forms


def test_flsa_selects_the_agreement(catalog) -> None:
    exempt = {
        r.result["form"]
        for r in catalog.matching("paperwork", {**CA_W2, "flsa": "Exempt"})
    }
    non_exempt = {r.result["form"] for r in catalog.matching("paperwork", CA_W2)}

    assert "Exempt employee agreement" in exempt
    assert "Non-exempt employee agreement" in non_exempt
    assert "Exempt employee agreement" not in non_exempt


def test_kit_matches_contract_type(catalog) -> None:
    # US-008 AC-001
    kits = catalog.matching("kit", CA_W2)

    assert len(kits) == 1
    assert kits[0].id.startswith("R-KT-")


def test_no_kit_rule_returns_nothing(catalog) -> None:
    # US-008 AC-002: no kit is presented as recommended
    assert catalog.matching("kit", {"employment_type": "Intern"}) == []


def test_owner_recommended_by_client_type_and_role(catalog) -> None:
    owners = catalog.matching(
        "owner", {"client_type": "Enterprise", "role": "Data Analyst"}
    )

    assert len(owners) == 1
    assert owners[0].result["owner"]


def test_overhead_is_two_or_five_percent(catalog) -> None:
    # BR-007
    rates = {
        r.result["provider"]: r.result["overhead_pct"]
        for r in catalog.rules("overhead")
    }

    assert rates == {"INSPYR": 2, "Apple Direct": 5}


def test_rule_ids_are_unique_and_well_formed(catalog) -> None:
    ids = [rule.id for rule in catalog.all()]

    assert len(ids) == len(set(ids))
    assert all(rule.cites_format() for rule in catalog.all())


def test_matching_ignores_case_and_spaces(catalog) -> None:
    shouted = {key: f"  {value.upper()} " for key, value in CA_W2.items()}

    assert catalog.matching("paperwork", shouted) == catalog.matching(
        "paperwork", CA_W2
    )
