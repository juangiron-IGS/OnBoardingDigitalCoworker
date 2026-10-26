"""US-012: the package is ready within 5 minutes of the last answer (FR-PKG-003)."""

from datetime import datetime

TARGET_SECONDS = 300


def package_timing(last_answer_at: datetime, package_at: datetime) -> dict:
    seconds = max(0, round((package_at - last_answer_at).total_seconds()))
    return {
        "seconds": seconds,
        "target_seconds": TARGET_SECONDS,
        "met": seconds <= TARGET_SECONDS,
    }
