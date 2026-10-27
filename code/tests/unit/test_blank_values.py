"""A blank, invisible or placeholder value is missing, never stored as data, so the
recruiter is asked for it (US-004, FR-VAL-004)."""

import pytest

from agents.common.model_client import clean_value, load_labels, read_labelled


@pytest.mark.parametrize("value", ["", "   ", "N/A", "n/a", "-", "TBD", "pending", "​"])
def test_placeholders_count_as_missing(value) -> None:
    assert clean_value(value) is None


def test_a_real_value_is_kept_trimmed() -> None:
    assert clean_value("  Acme Synthetic​ ") == "Acme Synthetic"


def test_a_labelled_placeholder_is_not_read_as_the_value() -> None:
    labels = load_labels()
    by_label = {
        alias.casefold(): f for f, aliases in labels.items() for alias in aliases
    }

    reading = read_labelled(
        "Client: N/A\nPosition: QA Engineer", list(labels), by_label
    )

    assert reading.values["client"] is None
    assert reading.values["role"] == "QA Engineer"
