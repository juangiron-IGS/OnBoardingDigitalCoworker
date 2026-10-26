from fastapi import APIRouter

from mcp_servers.mocks.teams.service import AlertsService

from ..deps import Conn, Role

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(conn: Conn, role: Role, case_id: str | None = None) -> list[dict]:
    """The simulated alerts view (FR-WEB-004). Alerts never hold restricted values."""
    return AlertsService(conn).list_alerts(case_id)
