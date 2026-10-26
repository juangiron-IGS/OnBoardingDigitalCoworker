import os

import psycopg
from fastapi import APIRouter, HTTPException

from ..deps import Conn

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
    return {
        "status": "ok",
        "database": "ok",
        # The web app always reads JobDiva in mock mode, in process; sandbox mode is
        # only served by the JobDiva READ server (mcp_servers/jobdiva_read).
        "jobdiva_mode": "mock",
        "model_provider": os.environ.get("MODEL_PROVIDER") or "rules",
    }
