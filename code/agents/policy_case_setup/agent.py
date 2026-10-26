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


# Values the Coworker never decides; a disagreement between sources is escalated.
ESCALATED_FIELDS = ("flsa", "employment_type")
CONFLICT_SOURCE = "email vs JobDiva start notes"


def find_conflicts(
    data: dict[str, object], notes: dict[str, object]
) -> dict[str, tuple[str, str]]:
    """FLSA or classification values that differ between the start and JobDiva."""
    return {
        field: (str(data[field]), str(notes[field]))
        for field in ESCALATED_FIELDS
        if data.get(field)
        and notes.get(field)
        and str(data[field]).strip().casefold() != str(notes[field]).strip().casefold()
    }


def recommend(
    data: dict[str, object],
    catalog: RulesCatalog,
    conflicts: dict[str, tuple[str, str]] | None = None,
) -> list[PackageLine]:
    conflicts = conflicts or {}
    channel = str(data.get("source_channel") or "email")
    answered = dict(data.get("answered_by") or {})
    lines = [
        _escalated(field, *conflicts[field])
        if field in conflicts
        else PackageLine(
            field=field,
            value=str(data[field]),
            label="source",
            source_or_rule_id=answered.get(field, channel),
        )
        for field in SOURCE_FIELDS
        if data.get(field)
    ]
    # A value in conflict must not pick a rule: that would decide it (BR-001).
    data = {k: v for k, v in data.items() if k not in conflicts}
    lines += _from_rules(catalog, "path", "path", "path", data)
    lines += _from_rules(catalog, "paperwork", "paperwork", "form", data)
    lines += _from_rules(catalog, "kit", "welcome_kit", "kit", data)
    owners = catalog.matching("owner", data)
    lines += [
        PackageLine(
            field="owner",
            value=rule.result["owner"],
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


def _escalated(field: str, stated: str, other: str) -> PackageLine:
    return PackageLine(
        field=field,
        value=(
            "Conflict escalated to the Onboarding Team and HR: the start email says "
            f"{stated}, the JobDiva start notes say {other}. No value selected."
        ),
        label="exception",
        source_or_rule_id=CONFLICT_SOURCE,
    )


def _no_rule(field: str) -> PackageLine:
    # US-008 AC-002: nothing is presented as recommended without a rule
    return PackageLine(
        field=field,
        value="No applicable rule found",
        label="exception",
        source_or_rule_id="rules catalog",
    )
