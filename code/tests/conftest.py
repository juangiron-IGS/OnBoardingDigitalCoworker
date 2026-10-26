import os
import uuid
from collections.abc import Iterator
from pathlib import Path

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


def _connect(url_var: str) -> psycopg.Connection:
    url = os.environ.get(url_var)
    if not url:
        pytest.fail(f"{url_var} is not set; copy code/.env.example to code/.env")
    try:
        return psycopg.connect(url)
    except psycopg.OperationalError as exc:
        pytest.fail(
            f"Cannot reach PostgreSQL ({url_var}); run ./scripts/start.sh: {exc}"
        )


@pytest.fixture
def app_conn() -> Iterator[psycopg.Connection]:
    """Application-role connection; each test's transaction is rolled back."""
    conn = _connect("DATABASE_URL")
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def audit_writer_conn() -> Iterator[psycopg.Connection]:
    conn = _connect("AUDIT_DATABASE_URL")
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def case_id() -> str:
    return f"test-{uuid.uuid4()}"
