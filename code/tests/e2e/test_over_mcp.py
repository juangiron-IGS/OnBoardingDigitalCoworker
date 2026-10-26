"""J1 and J2 with every system call over MCP (task B4, SAD Alternative B).

The MCP servers run in memory; the case service is local, as in the design.
Commits to the test database, so each run uses a fresh synthetic person.
"""

import os
import uuid

import psycopg
import pytest

from agents.common.mcp_adapters import McpAlerts, McpJobDivaRead, McpJobDivaWorkflow
from agents.common.mcp_client import McpToolClient
from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_read import server as jobdiva_read_server
from mcp_servers.jobdiva_workflow import server as workflow_server
from mcp_servers.mocks.teams import server as teams_server
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db


@pytest.fixture
def conn():
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as connection:
        yield connection


@pytest.fixture
def coworker(conn) -> Orchestrator:
    jobdiva = McpJobDivaRead(McpToolClient(jobdiva_read_server.server))
    return Orchestrator(
        cases=LocalCaseService(conn, jobdiva),
        model=RulesModelClient(load_labels(), UsageMeter(cap_per_run=50)),
        catalog=RulesCatalog.load(),
        alerts=McpAlerts(McpToolClient(teams_server.server)),
        workflow=McpJobDivaWorkflow(McpToolClient(workflow_server.server)),
        jobdiva=jobdiva,
    )


def _start(person: str, extra: str = "") -> str:
    return f"""Candidate ID: {person}
Position: QA Engineer
Hiring manager: Lee Example
Start date: 2026-12-14
Client: Acme Synthetic
Client type: Enterprise
Division: Digital
Line of business: Professional Services
Employment type: W-2
Vendor company: INSPYR Solutions
Work arrangement: Hybrid
Pay rate: 40.00 USD/h
Work city: Los Angeles
Work state: CA
FLSA: Non-exempt
Billing contact: billing.acme@example.com
Equipment: Standard laptop, INSPYR
Sponsorship: No
{extra}"""


def test_j1_and_j2_run_with_every_system_call_over_mcp(conn, coworker) -> None:
    person = f"SYN-M{uuid.uuid4().hex[:6]}"

    started = coworker.chat(_start(person))
    coworker.chat("61.00 USD/h", case_id=started.case_id)
    ready = coworker.chat("Lee Example", case_id=started.case_id)
    outcome = coworker.decide(
        started.case_id, package_version=1, decision="approve", approver_role="approver"
    )

    alert = conn.execute(
        "SELECT text FROM mocks.alerts WHERE case_id = %s AND recipient = 'Recruiter'",
        (started.case_id,),
    ).fetchone()[0]
    records = conn.execute(
        "SELECT count(*) FROM mocks.jobdiva_cases WHERE approval_id = %s",
        (outcome["approval_id"],),
    ).fetchone()[0]
    assert "Bill rate" in alert  # posted through the Teams MCP server
    assert ready.state == "ready_for_review"
    assert outcome["state"] == "actions_executed"
    assert records == 1  # written through the single-writer MCP server


def test_duplicate_in_jobdiva_is_found_over_mcp(coworker) -> None:
    reply = coworker.chat(
        "Candidate ID: SYN-0040\nStart date: 2026-11-02\nPosition: Analyst"
    )

    assert reply.state == "blocked_duplicate"
    assert "jobdiva:JD-START-1040" in reply.reply


def test_flsa_conflict_is_escalated_from_notes_read_over_mcp(conn, coworker) -> None:
    person = f"SYN-M{uuid.uuid4().hex[:6]}"
    text = _start(person, "Bill rate: 61.00 USD/h\nTimesheet approver: Lee Example\n")
    text += "JobDiva start ID: JD-START-1045\n"

    started = coworker.chat(text)

    status = conn.execute(
        "SELECT status FROM package_versions WHERE case_id = %s", (started.case_id,)
    ).fetchone()[0]
    assert status == "blocked"
