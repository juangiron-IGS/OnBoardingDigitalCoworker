"""The one place agents reach a model (Velocity 2.0 is the delivery method, not a
runtime). MODEL_PROVIDER picks the engine; agents only see ModelClient.

- rules (default): reads "Label: value" lines of the synthetic emails and chat
  messages. No model, no key, no cost; also what the tests use.
- claude: labelled lines first, then Claude (agents/common/claude_client.py) for
  the fields still missing. Needs ANTHROPIC_API_KEY in code/.env.
"""

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import yaml

from contracts.case_service_api import RESTRICTED_TERMS

from .usage_meter import UsageMeter

__all__ = ["RESTRICTED_TERMS"]

LABELS_FILE = (
    Path(__file__).resolve().parents[2] / "rules" / "intake" / "field_labels.yaml"
)
DEFAULT_CAP_PER_RUN = 50

_LINE = re.compile(r"^\s*([^:\n]{1,60}?)\s*:\s*(.+?)\s*$")


class ModelNotConfigured(Exception):
    """MODEL_PROVIDER names an engine that is not set up in this environment."""


@dataclass(frozen=True)
class Extraction:
    values: dict[str, str | None]
    ambiguous: list[str] = field(default_factory=list)


class ModelClient(Protocol):
    def extract_fields(
        self, text: str, fields: list[str], *, case_id: str, run_id: str
    ) -> Extraction:
        """Read the requested fields from untrusted text.

        A field with two different values is ambiguous: its value is None, so it
        is asked, never guessed (US-001 AC-002).
        """
        ...

    def pick_record(
        self, question: str, records: list[dict], *, run_id: str
    ) -> str | None:
        """US-025: the ID of the knowledge record that answers the question, "" when
        none does, or None when this engine does not choose (the agent then matches
        words). It only chooses: the answer is always the record's own text."""
        ...

    def converse(
        self,
        system: str,
        message: str,
        tools: list[dict],
        run_tool: Callable[[str, dict], str],
        *,
        run_id: str,
    ) -> str | None:
        """A conversational reply that may call the given read-only tools, or None
        when this engine does not converse (the chat then shows its help)."""
        ...


class RulesModelClient:
    """Deterministic engine for the synthetic, labelled emails and chat messages."""

    provider = "rules"

    def __init__(self, labels: dict[str, list[str]], meter: UsageMeter) -> None:
        self._by_label = {
            label.casefold(): name
            for name, aliases in labels.items()
            for label in aliases
        }
        self._meter = meter

    def extract_fields(
        self, text: str, fields: list[str], *, case_id: str, run_id: str
    ) -> Extraction:
        self._meter.record(run_id=run_id, case_id=case_id, provider=self.provider)
        return read_labelled(text, fields, self._by_label)

    def pick_record(
        self, question: str, records: list[dict], *, run_id: str
    ) -> str | None:
        return None  # no model: the knowledge agent matches words

    def converse(
        self,
        system: str,
        message: str,
        tools: list[dict],
        run_tool: Callable[[str, dict], str],
        *,
        run_id: str,
    ) -> str | None:
        return None  # no model: the chat keeps its fixed replies


def read_labelled(text: str, fields: list[str], by_label: dict[str, str]) -> Extraction:
    """The fields stated as "Label: value" lines; a field given twice with two
    different values is ambiguous."""
    found: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = _LINE.match(line)
        if not match:
            continue
        name = by_label.get(match.group(1).casefold())
        if name in fields:
            found.setdefault(name, set()).add(match.group(2))
    ambiguous = sorted(name for name, seen in found.items() if len(seen) > 1)
    values = {
        name: next(iter(found[name]))
        if name in found and name not in ambiguous
        else None
        for name in fields
    }
    return Extraction(values=values, ambiguous=ambiguous)


def _catalog(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_labels(path: Path = LABELS_FILE) -> dict[str, list[str]]:
    return _catalog(path)["fields"]


def load_required(path: Path = LABELS_FILE) -> list[str]:
    """Fields a case needs before it can be set up (FR-VAL-001, FR-VAL-002)."""
    return list(_catalog(path)["required"])


def get_model_client() -> ModelClient:
    provider = os.environ.get("MODEL_PROVIDER") or "rules"
    cap = int(os.environ.get("MODEL_USAGE_CAP_PER_RUN") or DEFAULT_CAP_PER_RUN)
    meter = UsageMeter(cap_per_run=cap)
    if provider == "rules":
        return RulesModelClient(load_labels(), meter)
    if provider == "claude":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ModelNotConfigured("MODEL_PROVIDER=claude needs ANTHROPIC_API_KEY")
        import anthropic

        from .claude_client import ClaudeModelClient

        # A key not scoped to a workspace names the workspace on every request.
        workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
        headers = {"anthropic-workspace-id": workspace} if workspace else None
        return ClaudeModelClient(
            load_labels(),
            meter,
            client=anthropic.Anthropic(default_headers=headers),
            model=os.environ.get("MODEL_EXTRACTION") or "claude-haiku-5-5",
        )
    raise ModelNotConfigured(
        f"MODEL_PROVIDER={provider!r} is unknown; use 'rules' or 'claude'"
    )
