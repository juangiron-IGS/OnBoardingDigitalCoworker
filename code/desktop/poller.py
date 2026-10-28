"""Reads the Coworker's alerts over MCP, as any other MCP client would.

The tray starts the onboarding-coworker server over stdio with the chosen role
(COWORKER_MCP_ROLE), so the server, not the tray, decides which alerts that role
receives. It calls only the read tool my_alerts: nothing is approved or changed.
"""

import asyncio
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters

CODE_DIR = Path(__file__).resolve().parents[1]
POLL_SECONDS = 5.0


def server_params(role: str) -> StdioServerParameters:
    env = {**os.environ, "COWORKER_MCP_ROLE": role, "PYTHONPATH": str(CODE_DIR)}
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.coworker.server", "--stdio"],
        env=env,
        cwd=str(CODE_DIR),
    )


async def fetch_alerts(
    client: Client, limit: int = 20, all_teams: bool = False
) -> list[dict]:
    """One call to my_alerts; a refusal or a bad reply reads as no alerts."""
    result = await client.call_tool(
        "my_alerts", {"limit": limit, "all_teams": all_teams}
    )
    if result.is_error:
        return []
    data: Any = result.structured_content
    if data is None and result.content:
        data = json.loads(result.content[0].text)
    if isinstance(data, dict):
        data = data.get("result", [])
    return [a for a in data or [] if isinstance(a, dict) and "id" in a]


async def poll(
    target: Any,  # noqa: ANN401 - StdioServerParameters, or a server in tests
    on_alerts: Callable[[list[dict]], None],
    on_status: Callable[[str], None],
    stop: asyncio.Event,
    interval: float = POLL_SECONDS,
    all_teams: bool = False,
) -> None:
    """Keep one MCP session open and pass every poll's alerts to on_alerts."""
    while not stop.is_set():
        try:
            async with Client(target, read_timeout_seconds=20) as client:
                on_status("connected")
                while not stop.is_set():
                    on_alerts(await fetch_alerts(client, all_teams=all_teams))
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=interval)
                    except TimeoutError:
                        pass
        except Exception:  # noqa: BLE001 - shown as disconnected, retried
            on_status("disconnected")
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
            except TimeoutError:
                pass
