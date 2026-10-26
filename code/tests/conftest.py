import os
import uuid
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _load_env_file() -> None:
    """Load code/.env into os.environ without overriding variables already set (CI)."""
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.split(" #", 1)[0].strip().strip('"')
        os.environ.setdefault(key.strip(), value)


_load_env_file()


def _use_test_database() -> None:
    """Point the suite at <DB_NAME>_test (or TEST_DB_NAME), never the dev database."""
    test_db = (
        os.environ.get("TEST_DB_NAME")
        or f"{os.environ.get('DB_NAME', 'coworker')}_test"
    )
    for var in ("DATABASE_URL", "AUDIT_DATABASE_URL"):
        if os.environ.get(var):
            url = urlsplit(os.environ[var])
            os.environ[var] = urlunsplit(url._replace(path=f"/{test_db}"))


_use_test_database()
# The suite never reaches a real JobDiva, whatever code/.env says.
os.environ["JOBDIVA_MODE"] = "mock"
# The API tests call the services in process; tests/e2e/test_over_mcp.py covers MCP.
os.environ["AGENT_TRANSPORT"] = "in_process"
# Should features are off unless a test turns one on.
os.environ["FEATURE_ACCESS_EQUIPMENT"] = "false"
# The suite never calls a real model or holds its key, whatever code/.env says.
os.environ["MODEL_PROVIDER"] = "rules"
os.environ.pop("ANTHROPIC_API_KEY", None)


def _connect(url_var: str) -> psycopg.Connection:
    url = os.environ.get(url_var)
    if not url:
        pytest.fail(f"{url_var} is not set; copy code/.env.example to code/.env")
    try:
        # Autocommit, like production: each use case owns its transactions.
        return psycopg.connect(url, autocommit=True)
    except psycopg.OperationalError as exc:
        pytest.fail(
            f"Cannot reach PostgreSQL ({url_var}); run ./scripts/start.sh: {exc}"
        )


@pytest.fixture
def app_conn() -> Iterator[psycopg.Connection]:
    """Application-role connection; everything a test writes is rolled back."""
    with _connect("DATABASE_URL") as conn, conn.transaction(force_rollback=True):
        yield conn


@pytest.fixture
def audit_writer_conn() -> Iterator[psycopg.Connection]:
    with _connect("AUDIT_DATABASE_URL") as conn, conn.transaction(force_rollback=True):
        yield conn


@pytest.fixture
def case_id() -> str:
    return f"test-{uuid.uuid4()}"
