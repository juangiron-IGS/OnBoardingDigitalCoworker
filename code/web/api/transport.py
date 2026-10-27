"""How the agents reach the systems: over MCP (SAD Alternative B), or in process as
the fallback behind the same interfaces (Alternative A). Set by AGENT_TRANSPORT."""

import socket
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

import psycopg

from agents.common.mcp_adapters import McpAlerts, McpJobDivaRead, McpJobDivaWorkflow
from agents.common.mcp_client import McpToolClient
from contracts.mcp_tools import Alerts, JobDivaRead, JobDivaWorkflow
from mcp_servers.jobdiva_read.adapters.mock import MockJobDiva
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.teams.service import AlertsService

TRANSPORTS = frozenset({"in_process", "mcp"})

# Server name -> (environment variable, default address). Loopback only.
_SERVERS = {
    "jobdiva-read": ("JOBDIVA_MOCK_URL", "http://127.0.0.1:8101"),
    "jobdiva-workflow": ("JOBDIVA_WORKFLOW_URL", "http://127.0.0.1:8106"),
    "teams-mock": ("TEAMS_MOCK_URL", "http://127.0.0.1:8108"),
    # The Coworker itself, for other chat apps; checked by the health endpoint only.
    "onboarding-coworker": ("COWORKER_MCP_URL", "http://127.0.0.1:8110"),
}

# In process, JobDiva is always read in mock mode; sandbox needs the READ server.
_mock_jobdiva = MockJobDiva()


@dataclass(frozen=True)
class Systems:
    jobdiva: JobDivaRead
    alerts: Alerts
    workflow: JobDivaWorkflow


def load_transport(env: Mapping[str, str]) -> str:
    transport = env.get("AGENT_TRANSPORT") or "in_process"
    if transport not in TRANSPORTS:
        raise ValueError(f"AGENT_TRANSPORT must be one of {sorted(TRANSPORTS)}")
    return transport


def mcp_urls(env: Mapping[str, str]) -> dict[str, str]:
    return {
        name: f"{(env.get(var) or default).rstrip('/')}/mcp"
        for name, (var, default) in _SERVERS.items()
    }


def systems(env: Mapping[str, str], conn: psycopg.Connection | None) -> Systems:
    if load_transport(env) == "in_process":
        return Systems(
            jobdiva=_mock_jobdiva,
            alerts=AlertsService(conn),
            workflow=WorkflowService(conn),
        )
    clients = {
        name: McpToolClient(url, name=name) for name, url in mcp_urls(env).items()
    }
    return Systems(
        jobdiva=McpJobDivaRead(clients["jobdiva-read"]),
        alerts=McpAlerts(clients["teams-mock"]),
        workflow=McpJobDivaWorkflow(clients["jobdiva-workflow"]),
    )


def reachable(url: str, timeout: float = 1.0) -> bool:
    """Is something listening at this address? Used by the health check only."""
    address = urlsplit(url)
    try:
        with socket.create_connection(
            (address.hostname or "127.0.0.1", address.port or 80), timeout=timeout
        ):
            return True
    except OSError:
        return False
