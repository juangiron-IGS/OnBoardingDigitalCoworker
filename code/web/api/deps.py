import os
from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, Header, HTTPException

from agents.common.model_client import get_model_client
from agents.orchestrator.orchestrator import Orchestrator
from contracts.mcp_tools import KnowledgeBase
from mcp_servers.common.db import connect
from mcp_servers.mocks.outlook.service import MailboxService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.privacy import ROLES
from services.case_service.service import LocalCaseService

from .transport import systems

_catalog = RulesCatalog.load()


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
    return LocalCaseService(conn, systems(os.environ, conn).jobdiva)


def get_orchestrator(conn: Conn) -> Orchestrator:
    wired = systems(os.environ, conn)
    return Orchestrator(
        cases=LocalCaseService(conn, wired.jobdiva),
        model=get_model_client(),
        catalog=_catalog,
        alerts=wired.alerts,
        workflow=wired.workflow,
        jobdiva=wired.jobdiva,
        knowledge=wired.knowledge,
    )


def get_mailbox(conn: Conn) -> MailboxService:
    return MailboxService(conn=conn)


Cases = Annotated[LocalCaseService, Depends(get_cases)]
Coworker = Annotated[Orchestrator, Depends(get_orchestrator)]
Mailbox = Annotated[MailboxService, Depends(get_mailbox)]


def get_knowledge(conn: Conn) -> KnowledgeBase:
    return systems(os.environ, conn).knowledge


Knowledge = Annotated[KnowledgeBase, Depends(get_knowledge)]
