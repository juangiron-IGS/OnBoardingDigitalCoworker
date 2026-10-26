import os

import psycopg
from fastapi import APIRouter, HTTPException

from ..deps import Conn
from ..transport import load_transport, mcp_urls, reachable

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health(conn: Conn) -> dict:
    """Used by scripts/health_check.py after start. Reports settings, never secrets."""
    try:
        conn.execute("SELECT 1").fetchone()
    except psycopg.Error:
        raise HTTPException(
            503, detail={"status": "down", "database": "down"}
        ) from None
    transport = load_transport(os.environ)
    body = {
        "status": "ok",
        "database": "ok",
        "transport": transport,
        # In process, JobDiva is always read in mock mode; over MCP the JobDiva READ
        # server reads it in the mode it was started with.
        "jobdiva_mode": "mock"
        if transport == "in_process"
        else os.environ.get("JOBDIVA_MODE") or "mock",
        "model_provider": os.environ.get("MODEL_PROVIDER") or "rules",
    }
    if transport == "mcp":
        servers = {
            name: "ok" if reachable(url) else "down"
            for name, url in mcp_urls(os.environ).items()
        }
        body["mcp_servers"] = servers
        if "down" in servers.values():
            body["status"] = "degraded"
    return body
