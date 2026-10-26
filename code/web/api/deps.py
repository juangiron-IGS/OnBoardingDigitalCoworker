from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, Header, HTTPException

from agents.common.model_client import get_model_client
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.common.db import connect
from mcp_servers.jobdiva_read.adapters.mock import MockJobDiva
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.outlook.service import MailboxService
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.privacy import ROLES
from services.case_service.service import LocalCaseService

_catalog = RulesCatalog.load()


# JobDiva in mock mode, in process. Sandbox mode runs the JobDiva READ server.
_jobdiva = MockJobDiva()


def get_conn() -> Iterator[psycopg.Connection]:
    with connect() as conn:
        yield conn


Conn = Annotated[psycopg.Connection, Depends(get_conn)]


def get_role(x_role: Annotated[str, Header()]) -> str:
    """The simulated role selector; the case service applies the policy."""
    if x_role not in ROLES:
        raise HTTPException(400, detail=f"X-Role must be one of {sorted(ROLES)}")
    return x_role


Role = Annotated[str, Depends(get_role)]


def get_cases(conn: Conn) -> LocalCaseService:
    return LocalCaseService(conn, _jobdiva)


def get_orchestrator(conn: Conn) -> Orchestrator:
    return Orchestrator(
        cases=LocalCaseService(conn, _jobdiva),
        model=get_model_client(),
        catalog=_catalog,
        alerts=AlertsService(conn),
        workflow=WorkflowService(conn),
        jobdiva=_jobdiva,
    )


def get_mailbox() -> MailboxService:
    return MailboxService()


Cases = Annotated[LocalCaseService, Depends(get_cases)]
Coworker = Annotated[Orchestrator, Depends(get_orchestrator)]
Mailbox = Annotated[MailboxService, Depends(get_mailbox)]
