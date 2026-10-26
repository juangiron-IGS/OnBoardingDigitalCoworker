"""How agents call MCP tools (task B4). The target is a URL at run time, or an
in-memory server in tests; the agents never know which."""

import asyncio
import json
from typing import Any

from mcp import Client
from mcp.server.mcpserver import MCPServer

# What an MCP tool returns once decoded from JSON.
ToolResult = dict[str, Any] | list[Any] | str | int | float | bool | None


class McpCallFailed(Exception):
    """A server could not be reached or its tool failed. The step fails visibly."""


class McpToolClient:
    def __init__(
        self, target: str | MCPServer, *, name: str | None = None, timeout: float = 20
    ) -> None:
        self._target = target
        self._name = name or (target if isinstance(target, str) else target.name)
        self._timeout = timeout

    def call(self, tool: str, arguments: dict[str, Any]) -> ToolResult:
        try:
            return asyncio.run(self._call(tool, arguments))
        except McpCallFailed:
            raise
        except Exception as exc:  # noqa: BLE001 - any transport failure is reported the same way
            raise McpCallFailed(
                f"{self._name}: {tool} failed ({type(exc).__name__})"
            ) from exc

    async def _call(self, tool: str, arguments: dict[str, Any]) -> ToolResult:
        async with Client(self._target, read_timeout_seconds=self._timeout) as client:
            result = await client.call_tool(tool, arguments)
        if result.is_error:
            raise McpCallFailed(f"{self._name}: {tool} returned an error")
        data = result.structured_content
        if data is None:
            data = json.loads(result.content[0].text) if result.content else None
        if isinstance(data, dict) and set(data) == {"result"}:
            data = data["result"]
        return data
