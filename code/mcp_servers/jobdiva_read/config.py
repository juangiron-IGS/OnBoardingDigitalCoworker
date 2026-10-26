"""JOBDIVA_MODE is read once at startup and never switched while running (ADR-004)."""

from collections.abc import Mapping

ALLOWED_MODES = ("mock", "sandbox")


def load_mode(env: Mapping[str, str]) -> str:
    """Return the mode, mock by default. Any other value stops the process."""
    mode = env.get("JOBDIVA_MODE") or "mock"
    if mode not in ALLOWED_MODES:
        raise SystemExit(
            f"JOBDIVA_MODE must be one of {list(ALLOWED_MODES)}, got {mode!r}"
        )
    return mode
