"""US-012 AC-001 and AC-003: the package is ready within 5 minutes of the last answer,
and a late one is reported as missing the target."""

from datetime import UTC, datetime, timedelta

from services.case_service.domain.timing import TARGET_SECONDS, package_timing

LAST_ANSWER = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)


def test_package_within_five_minutes_meets_the_target() -> None:
    timing = package_timing(LAST_ANSWER, LAST_ANSWER + timedelta(seconds=4))

    assert timing == {"seconds": 4, "target_seconds": 300, "met": True}


def test_late_package_is_reported_as_missing_the_target() -> None:
    timing = package_timing(LAST_ANSWER, LAST_ANSWER + timedelta(minutes=6))

    assert timing["met"] is False
    assert timing["seconds"] == 360


def test_target_is_five_minutes() -> None:
    assert TARGET_SECONDS == 300
