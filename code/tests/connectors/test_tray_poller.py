"""Coworker Tray reads alerts over MCP from the onboarding-coworker server; the
server's role decides which alerts it gets. Commits to the test database."""

import asyncio
import uuid

import pytest
from mcp import Client

from desktop.poller import fetch_alerts, server_params
from mcp_servers.common.db import connect
from mcp_servers.coworker import server as coworker_server
from mcp_servers.mocks.teams.service import AlertsService

pytestmark = pytest.mark.db


async def _alerts() -> list[dict]:
    async with Client(coworker_server.server) as client:
        return await fetch_alerts(client)


def test_tray_gets_only_its_role_alerts(monkeypatch) -> None:
    case_id = f"case-tray-{uuid.uuid4().hex[:6]}"
    with connect() as conn:
        AlertsService(conn).post_alert(case_id, "IT", "Laptop request waits for you.")
        AlertsService(conn).post_alert(case_id, "Recruiter", "Missing: Bill rate.")

    monkeypatch.setenv("COWORKER_MCP_ROLE", "it")
    it_alerts = asyncio.run(_alerts())
    monkeypatch.setenv("COWORKER_MCP_ROLE", "recruiter")
    recruiter_alerts = asyncio.run(_alerts())

    mine = [a["text"] for a in it_alerts if a["case_id"] == case_id]
    theirs = [a["text"] for a in recruiter_alerts if a["case_id"] == case_id]
    assert mine == ["Laptop request waits for you."]
    assert theirs == ["Missing: Bill rate."]


def test_the_tray_starts_the_server_with_its_role() -> None:
    params = server_params("ldc")

    assert params.args == ["-m", "mcp_servers.coworker.server", "--stdio"]
    assert params.env["COWORKER_MCP_ROLE"] == "ldc"
