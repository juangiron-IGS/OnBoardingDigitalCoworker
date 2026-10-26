"""Policy and Case Setup agent (Must): path, paperwork, kit and owner from the rules
catalog, each citing its rule (US-007, US-008, US-010). It never decides FLSA,
classification or compensation: those values are copied from the source only
(BR-001)."""

from contracts.case_service_api import PackageLine
from services.case_service.adapters.rules_files.catalog import RulesCatalog

AGENT = "policy_case_setup"

# Data points shown in the package as they came from the start (label "source").
SOURCE_FIELDS = [
    "client",
    "role",
    "start_date",
    "employment_type",
    "work_city",
    "work_state",
    "work_arrangement",
    "flsa",
    "sponsorship_visa",
]


def recommend(data: dict[str, object], catalog: RulesCatalog) -> list[PackageLine]:
    origin = str(data.get("source_channel") or "email")
    lines = [
        PackageLine(
            field=field,
            value=str(data[field]),
            label="source",
            source_or_rule_id=origin,
        )
        for field in SOURCE_FIELDS
        if data.get(field)
    ]
    lines += _from_rules(catalog, "path", "path", "path", data)
    lines += _from_rules(catalog, "paperwork", "paperwork", "form", data)
    lines += _from_rules(catalog, "kit", "welcome_kit", "kit", data)
    owners = catalog.matching("owner", data)
    lines += [
        PackageLine(
            field="owner",
            value=f"{rule.result['owner']} (recommended, pending assignment)",
            label="recommended",
            source_or_rule_id=rule.id,
        )
        for rule in owners
    ] or [_no_rule("owner")]
    return lines


def _from_rules(
    catalog: RulesCatalog, domain: str, field: str, key: str, data: dict
) -> list[PackageLine]:
    rules = catalog.matching(domain, data)
    if not rules:
        return [_no_rule(field)]
    return [
        PackageLine(
            field=field,
            value=str(rule.result[key]),
            label="recommended",
            source_or_rule_id=rule.id,
        )
        for rule in rules
    ]


def _no_rule(field: str) -> PackageLine:
    # US-008 AC-002: nothing is presented as recommended without a rule
    return PackageLine(
        field=field,
        value="No applicable rule found",
        label="exception",
        source_or_rule_id="rules catalog",
    )
