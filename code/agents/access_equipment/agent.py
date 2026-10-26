"""Access and Equipment agent (Should, S1): the access and laptop request for IT
approval, with equipment overhead and bill-back from the rules (US-020, US-021)."""

from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.package import PackageLine

AGENT = "access_equipment"
FIELDS = ("equipment_request", "equipment_overhead", "bill_back")


def _equipment(data: dict, catalog: RulesCatalog) -> tuple[str, str] | None:
    """The start's equipment as (hardware tier, provider): 'Standard laptop, INSPYR',
    or free text naming a provider from the overhead rules ('laptop from INSPYR')."""
    text = str(data.get("equipment") or "").strip()
    if not text:
        return None
    tier, _, provider = text.rpartition(",")
    if tier:
        return tier.strip(), provider.strip()
    for known in {str(r.result["provider"]) for r in catalog.rules("overhead")}:
        at = text.casefold().find(known.casefold())
        if at >= 0:
            tier = text[:at].strip().removesuffix("from").removesuffix("via").strip()
            return tier or text, known
    return text, ""


def _exception(field: str, text: str) -> PackageLine:
    return PackageLine(
        field=field, value=text, label="exception", source_or_rule_id="rules catalog"
    )


def recommend(data: dict, catalog: RulesCatalog) -> list[PackageLine]:
    equipment = _equipment(data, catalog)
    if equipment is None:
        return []
    tier, provider = equipment
    lines = []

    access = catalog.matching("access", data)
    lines.append(
        PackageLine(
            field="equipment_request",
            value=(
                f"{access[0].result['provider']} laptop: {tier}; "
                f"access: {access[0].result['access']}"
            ),
            label="recommended",
            source_or_rule_id=access[0].id,
        )
        if access
        else _exception("equipment_request", "No access rule; IT to prepare it")
    )

    overhead = catalog.matching("overhead", data | {"equipment_provider": provider})
    lines.append(
        PackageLine(
            field="equipment_overhead",
            value=f"{overhead[0].result['overhead_pct']}% ({provider})",
            label="recommended",
            source_or_rule_id=overhead[0].id,
        )
        if overhead
        else _exception(
            "equipment_overhead", f"No overhead rule for provider {provider or '?'}"
        )
    )

    bill_back = catalog.matching("billback", data)
    lines.append(
        PackageLine(
            field="bill_back",
            value=str(bill_back[0].result["bill_back"]),
            label="recommended",
            source_or_rule_id=bill_back[0].id,
        )
        if bill_back
        else _exception(
            "bill_back", "No bill-back rule for this client; Onboarding Team to decide"
        )
    )
    return lines


def it_request(data: dict, catalog: RulesCatalog) -> dict[str, str]:
    """Payload of the simulated Chelsea Tech request. No restricted fields."""
    tier, provider = _equipment(data, catalog) or ("", "")
    access = catalog.matching("access", data)
    return {
        "provider": str(access[0].result["provider"]) if access else "",
        "hardware": tier,
        "supplier": provider,
        "access": str(access[0].result["access"]) if access else "",
    }
