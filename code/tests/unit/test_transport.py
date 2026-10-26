"""AGENT_TRANSPORT picks how the agents reach the systems (task B4)."""

import pytest

from agents.common.mcp_adapters import McpAlerts, McpJobDivaRead, McpJobDivaWorkflow
from mcp_servers.jobdiva_read.adapters.mock import MockJobDiva
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.teams.service import AlertsService
from web.api.transport import load_transport, mcp_urls, systems


def test_transport_defaults_to_in_process() -> None:
    assert load_transport({}) == "in_process"


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(ValueError, match="AGENT_TRANSPORT"):
        load_transport({"AGENT_TRANSPORT": "grpc"})


def test_in_process_uses_the_services_directly() -> None:
    wired = systems({"AGENT_TRANSPORT": "in_process"}, conn=None)

    assert isinstance(wired.jobdiva, MockJobDiva)
    assert isinstance(wired.alerts, AlertsService)
    assert isinstance(wired.workflow, WorkflowService)


def test_mcp_uses_the_adapters() -> None:
    wired = systems({"AGENT_TRANSPORT": "mcp"}, conn=None)

    assert isinstance(wired.jobdiva, McpJobDivaRead)
    assert isinstance(wired.alerts, McpAlerts)
    assert isinstance(wired.workflow, McpJobDivaWorkflow)


def test_mcp_urls_come_from_the_environment() -> None:
    urls = mcp_urls({"JOBDIVA_MOCK_URL": "http://127.0.0.1:9101/"})

    assert urls["jobdiva-read"] == "http://127.0.0.1:9101/mcp"
    assert urls["jobdiva-workflow"] == "http://127.0.0.1:8106/mcp"
    assert urls["teams-mock"] == "http://127.0.0.1:8108/mcp"
