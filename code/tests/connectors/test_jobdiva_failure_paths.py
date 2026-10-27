"""JobDiva connector: error paths, startup and the production-URL refusal.

Complements test_jobdiva_read.py. Cases: QC-SEC-N-001 (no secret in error paths),
QC-SEC-N-002 (startup per JOBDIVA_MODE), QC-ACT-N-002 (no outbound call in mock
mode), QC-REL-N-001 (a failing JobDiva is never replaced by mock data) and
QC-COMP-N-001 (a production URL is refused).
"""

import contextlib
import logging
import os
import socket
import subprocess  # noqa: S404 - starts our own server module to test its startup
import sys
from datetime import date
from pathlib import Path

import httpx
import pytest

from mcp_servers.jobdiva_read.adapters.mock import MockJobDiva
from mcp_servers.jobdiva_read.adapters.sandbox import SandboxJobDiva

CODE_DIR = Path(__file__).resolve().parents[2]
SECRET_PASSWORD = "canary-pa55word-td013"  # noqa: S105 - synthetic canary (TD-013)
SECRET_TOKEN = "canary-token-td013"  # noqa: S105 - synthetic canary (TD-013)
PRODUCTION_URL = "https://api.jobdiva.com"  # the host `.env.example` names


def _sandbox(handler, base_url: str = "https://api.jobdiva.example") -> SandboxJobDiva:
    return SandboxJobDiva(
        base_url=base_url,
        client_id="client-1",
        api_user="api-user@example.com",
        api_password=SECRET_PASSWORD,
        transport=httpx.MockTransport(handler),
    )


def _authenticated(read_response):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/authenticate"):
            return httpx.Response(200, text=SECRET_TOKEN)
        return read_response(request)

    return handler


@pytest.mark.xfail(
    strict=True,
    reason="DEF-002: the sign-in call sends the API password in the query string, "
    "so the error from raise_for_status carries it (QC-SEC-N-001, NFR-SEC-005)",
)
def test_failed_authentication_does_not_expose_the_password(caplog) -> None:
    # QC-SEC-N-001 step 1-2: the error path of the sign-in call
    caplog.set_level(logging.DEBUG)
    jobdiva = _sandbox(lambda request: httpx.Response(401))

    with pytest.raises(Exception) as failure:  # noqa: B017, PT011 - any visible error
        jobdiva.read_start("JD-1")

    assert SECRET_PASSWORD not in str(failure.value)
    assert SECRET_PASSWORD not in caplog.text


def test_failed_read_does_not_expose_the_token(caplog) -> None:
    # QC-SEC-N-001: the error path of a read after sign-in
    caplog.set_level(logging.DEBUG)
    jobdiva = _sandbox(_authenticated(lambda request: httpx.Response(500)))

    with pytest.raises(httpx.HTTPStatusError) as failure:
        jobdiva.read_start("JD-1")

    for text in (str(failure.value), caplog.text, repr(jobdiva)):
        assert SECRET_TOKEN not in text
        assert SECRET_PASSWORD not in text


def test_unreachable_jobdiva_fails_visibly_and_never_falls_back_to_mock() -> None:
    # QC-REL-N-001 step 3: no silent switch to mock data
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("JobDiva unavailable", request=request)

    jobdiva = _sandbox(down)

    with pytest.raises(httpx.ConnectError):
        jobdiva.read_start("JD-START-1042")
    with pytest.raises(httpx.ConnectError):
        jobdiva.search_duplicate("SYN-0040", date(2026, 11, 2))


def test_mock_mode_never_opens_a_network_connection(monkeypatch) -> None:
    # QC-ACT-N-002 step 1: nothing leaves the machine in mock mode
    def refuse(*args, **kwargs):
        raise AssertionError("the mock connector tried to open a connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    jobdiva = MockJobDiva()

    assert jobdiva.read_start("JD-START-1042")["person_ref"] == "SYN-0042"
    assert jobdiva.read_start_notes("JD-START-1042")
    assert jobdiva.search_duplicate("SYN-0040", date(2026, 11, 2))["found"] is True


@pytest.mark.parametrize("value", ["production", "write", "Mock", ""])
def test_server_process_stops_on_an_invalid_mode(value: str) -> None:
    # QC-SEC-N-002 step 2: a real start, not only the loader function
    env = {**os.environ, "JOBDIVA_MODE": value or "invalid"}

    result = subprocess.run(  # noqa: S603 - fixed module, no user input
        [sys.executable, "-m", "mcp_servers.jobdiva_read.server"],
        cwd=CODE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode != 0
    assert "JOBDIVA_MODE" in result.stderr


@pytest.mark.xfail(
    strict=True,
    reason="DEF-001: nothing validates JOBDIVA_BASE_URL, so the production "
    "host is accepted (Test Cases QC-COMP-N-001, NFR-COMP-001)",
)
def test_production_url_is_refused_and_nothing_is_sent() -> None:
    # QC-COMP-N-001: expected to fail until a refusal is built
    sent: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, text=SECRET_TOKEN, json={"data": []})

    refused = False
    with contextlib.suppress(Exception):
        _sandbox(record, base_url=PRODUCTION_URL).read_start("JD-1")
    # A refusal at construction or at the first call both count; a request does not.
    refused = not sent

    assert refused, "a request was sent to the production host"
