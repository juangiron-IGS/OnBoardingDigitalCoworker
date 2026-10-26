"""Rules catalog: business rules kept as data in code/rules/ (BR-006, FR-REC-005).

Each rule file holds one domain (paperwork, path, kit, owner, overhead). A rule
applies when every condition in `when` equals the case value, ignoring case and
surrounding spaces; a key that is not in `when` matches anything.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from ...domain.package import RULE_ID

RULES_ROOT = Path(__file__).resolve().parents[4] / "rules"


class Rule(BaseModel):
    id: str = Field(pattern=r"^R-[A-Z]+-\d+$")
    domain: str = Field(min_length=1, max_length=32)
    owner: Literal["Onboarding", "IT", "LDC"]
    version: int = Field(ge=1)
    status: Literal["draft", "approved"]
    when: dict[str, str] = Field(default_factory=dict)
    result: dict[str, str | int | float]
    note: str | None = Field(default=None, max_length=500)

    def cites_format(self) -> bool:
        return RULE_ID.fullmatch(self.id) is not None

    def applies_to(self, case: dict[str, object]) -> bool:
        return all(
            _norm(case.get(key)) == _norm(value) for key, value in self.when.items()
        )


def _norm(value: object) -> str:
    return "" if value is None else str(value).strip().casefold()


class RulesCatalog:
    def __init__(self, rules: list[Rule]) -> None:
        self._by_id: dict[str, Rule] = {}
        for rule in rules:
            if rule.id in self._by_id:
                raise ValueError(f"duplicate rule id {rule.id}")
            self._by_id[rule.id] = rule

    @classmethod
    def load(cls, root: Path = RULES_ROOT) -> "RulesCatalog":
        rules: list[Rule] = []
        for path in sorted(root.rglob("*.yaml")):
            with path.open(encoding="utf-8") as handle:
                doc = yaml.safe_load(handle) or {}
            if "domain" not in doc:
                continue  # not a rules file, e.g. rules/intake/field_labels.yaml
            rules.extend(
                Rule(domain=doc["domain"], **entry) for entry in doc.get("rules", [])
            )
        return cls(rules)

    def all(self) -> list[Rule]:
        return sorted(self._by_id.values(), key=lambda rule: rule.id)

    def ids(self) -> set[str]:
        return set(self._by_id)

    def get(self, rule_id: str) -> Rule:
        return self._by_id[rule_id]

    def rules(self, domain: str) -> list[Rule]:
        return [rule for rule in self.all() if rule.domain == domain]

    def matching(self, domain: str, case: dict[str, object]) -> list[Rule]:
        return [rule for rule in self.rules(domain) if rule.applies_to(case)]
