"""Intake and Validation agent (Must): reads the start, checks completeness and
contradictions (US-001, US-004, US-005). The checks are deterministic; the model
client only reads fields from the untrusted text."""

from dataclasses import dataclass

from agents.common.model_client import ModelClient

AGENT = "intake_validation"


@dataclass(frozen=True)
class IntakeReading:
    values: dict[str, str]
    missing: list[str]
    contradictions: list[str]


def read_start(
    text: str,
    *,
    model: ModelClient,
    fields: list[str],
    required: list[str],
    case_id: str,
    run_id: str,
) -> IntakeReading:
    extraction = model.extract_fields(text, fields, case_id=case_id, run_id=run_id)
    values = {k: v for k, v in extraction.values.items() if v is not None}
    return IntakeReading(
        values=values,
        missing=missing_fields(values, required, extraction.ambiguous),
        contradictions=list(extraction.ambiguous),
    )


def missing_fields(
    values: dict[str, object], required: list[str], contradictions: list[str] = ()
) -> list[str]:
    """Required fields with no confirmed value, contradictions excluded."""
    return sorted(f for f in required if not values.get(f) and f not in contradictions)
