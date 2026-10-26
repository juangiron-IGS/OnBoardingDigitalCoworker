"""JobDiva READ server: mock by default, read-only sandbox (US-035, BR-014)."""

import logging
from datetime import date

import httpx
import pytest

from contracts.mcp_tools import JobDivaRead
from mcp_servers.jobdiva_read.adapters.mock import MockJobDiva
from mcp_servers.jobdiva_read.adapters.sandbox import ReadOnlyViolation, SandboxJobDiva
from mcp_servers.jobdiva_read.config import load_mode

SECRET_PASSWORD = "s3cret-pa55word-x"  # noqa: S105 - synthetic test value
SECRET_TOKEN = "tok-9f8e7d6c5b4a-synthetic"  # noqa: S105 - synthetic test value


def test_mock_is_the_default_mode() -> None:
    # US-035 AC-001
    assert load_mode({}) == "mock"


@pytest.mark.parametrize("value", ["sandbox", "mock"])
def test_known_modes_are_accepted(value: str) -> None:
    assert load_mode({"JOBDIVA_MODE": value}) == value


@pytest.mark.parametrize("value", ["production", "write", "MOCK "])
def test_any_other_mode_stops_the_process(value: str) -> None:
    with pytest.raises(SystemExit):
        load_mode({"JOBDIVA_MODE": value})


def test_mock_reads_a_start_and_its_notes() -> None:
    jobdiva = MockJobDiva()

    start = jobdiva.read_start("JD-START-1042")
    notes = jobdiva.read_start_notes("JD-START-1042")

    assert start["person_ref"] == "SYN-0042"
    assert notes["work_state"] == "CA"


def test_mock_duplicate_search_finds_an_onboarding_in_jobdiva() -> None:
    # US-017 AC-001: a case already in JobDiva blocks the start
    found = MockJobDiva().search_duplicate("SYN-0040", date(2026, 11, 2))

    assert found == {"found": True, "start_id": "JD-START-1040"}


def test_mock_duplicate_search_is_negative_for_a_new_person() -> None:
    found = MockJobDiva().search_duplicate("SYN-0042", date(2026, 11, 2))

    assert found == {"found": False, "start_id": None}


def test_both_adapters_fulfil_the_read_contract() -> None:
    assert isinstance(MockJobDiva(), JobDivaRead)
    assert isinstance(_sandbox(lambda request: httpx.Response(200)), JobDivaRead)


def _fake_jobdiva(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/authenticate"):
        return httpx.Response(200, text=SECRET_TOKEN)
    assert request.headers["Authorization"] == f"Bearer {SECRET_TOKEN}"
    return httpx.Response(
        200, json={"data": [{"STARTID": "JD-1", "CANDIDATEID": "SYN-1"}]}
    )


def _sandbox(handler) -> SandboxJobDiva:
    return SandboxJobDiva(
        base_url="https://api.jobdiva.example",
        client_id="client-1",
        api_user="api-user@example.com",
        api_password=SECRET_PASSWORD,
        transport=httpx.MockTransport(handler),
    )


def test_sandbox_reads_with_a_token_kept_in_memory(caplog) -> None:
    # US-035 AC-003: no token or password in any log
    caplog.set_level(logging.DEBUG)
    jobdiva = _sandbox(_fake_jobdiva)

    start = jobdiva.read_start("JD-1")

    assert start["STARTID"] == "JD-1"
    assert SECRET_TOKEN not in caplog.text
    assert SECRET_PASSWORD not in caplog.text
    assert SECRET_TOKEN not in repr(jobdiva)


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_sandbox_refuses_every_write(method: str, caplog) -> None:
    # US-035 AC-002, BR-014: the connector refuses writes and logs the refusal
    caplog.set_level(logging.WARNING)
    jobdiva = _sandbox(_fake_jobdiva)

    with pytest.raises(ReadOnlyViolation):
        jobdiva.request(method, "/apiv2/jobdiva/onboarding")

    assert "refused" in caplog.text
    assert SECRET_TOKEN not in caplog.text
