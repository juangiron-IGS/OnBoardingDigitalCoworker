"""Read model for the web views: cases, their current package, audit trail and the
records the single writer created. Read only."""

from datetime import datetime
from typing import Any

import psycopg

from ...domain.timing import package_timing

MOCK_STORES = (
    "jobdiva_cases",
    "task_lists",
    "it_requests",
    "payroll_packages",
    "ldc_tracker",
    "welcome_kits",
)


def _timing(
    last_answer_at: datetime | None, package_at: datetime | None
) -> dict | None:
    """From the last start data or answer to the current package (US-012)."""
    if last_answer_at is None or package_at is None:
        return None
    return package_timing(last_answer_at, package_at)


def list_cases(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT c.id, c.person_ref, c.start_date, c.state,"
        " c.current_package_version, c.created_at, last.at, p.created_at,"
        " c.data->>'candidate_name', c.data->>'role'"
        " FROM cases c"
        " LEFT JOIN package_versions p"
        "   ON p.case_id = c.id AND p.version = c.current_package_version"
        " LEFT JOIN LATERAL (SELECT max(a.recorded_at) AS at FROM audit_log a"
        "   WHERE a.case_id = c.id AND a.action IN ('create_case', 'record_answers')"
        "   AND a.recorded_at <= p.created_at) last ON true"
        " ORDER BY c.created_at DESC LIMIT 200"
    ).fetchall()
    return [
        {
            "id": r[0],
            "person_ref": r[1],
            "start_date": r[2].isoformat(),
            "state": r[3],
            "package_version": r[4],
            "created_at": r[5].isoformat(),
            "package_timing": _timing(r[6], r[7]),
            "candidate_name": r[8],
            "role": r[9],
        }
        for r in rows
    ]


def find_case(conn: psycopg.Connection, ref: str) -> str | None:
    """A case by its ID or, latest first, by the candidate reference."""
    row = conn.execute(
        "SELECT id FROM cases WHERE id = %s OR person_ref = %s"
        " ORDER BY created_at DESC LIMIT 1",
        (ref, ref),
    ).fetchone()
    return row[0] if row else None


def case_detail(conn: psycopg.Connection, case_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT c.id, c.person_ref, c.start_date, c.state, c.current_package_version,"
        " c.data, c.recommended_owner, c.assigned_owner, last.at, p.created_at"
        " FROM cases c"
        " LEFT JOIN package_versions p"
        "   ON p.case_id = c.id AND p.version = c.current_package_version"
        " LEFT JOIN LATERAL (SELECT max(a.recorded_at) AS at FROM audit_log a"
        "   WHERE a.case_id = c.id AND a.action IN ('create_case', 'record_answers')"
        "   AND a.recorded_at <= p.created_at) last ON true"
        " WHERE c.id = %s",
        (case_id,),
    ).fetchone()
    if row is None:
        return None
    case = {
        "id": row[0],
        "person_ref": row[1],
        "start_date": row[2].isoformat(),
        "state": row[3],
        "package_version": row[4],
        "data": row[5],
        "recommended_owner": row[6],
        "assigned_owner": row[7],
        "package_timing": _timing(row[8], row[9]),
        "it_approved": conn.execute(
            "SELECT 1 FROM it_approvals WHERE case_id = %s AND package_version = %s",
            (case_id, row[4]),
        ).fetchone()
        is not None,
    }
    return {
        "case": case,
        "package": package(conn, case_id, row[4]),
        "audit": _audit(conn, case_id),
        "records": _records(conn, case_id),
    }


def package(conn: psycopg.Connection, case_id: str, version: int) -> dict | None:
    if version == 0:
        return None
    status = conn.execute(
        "SELECT status FROM package_versions WHERE case_id = %s AND version = %s",
        (case_id, version),
    ).fetchone()[0]
    lines = conn.execute(
        "SELECT field, value, label, source_or_rule_id FROM package_lines"
        " WHERE case_id = %s AND version = %s ORDER BY id",
        (case_id, version),
    ).fetchall()
    return {
        "version": version,
        "status": status,
        "lines": [
            {"field": f, "value": v, "label": lab, "source_or_rule_id": src}
            for f, v, lab, src in lines
        ],
    }


def _audit(conn: psycopg.Connection, case_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT agent, action, outcome, approval_id, package_version, rule_ids,"
        " recorded_at FROM audit_log WHERE case_id = %s ORDER BY id",
        (case_id,),
    ).fetchall()
    return [
        {
            "agent": r[0],
            "action": r[1],
            "outcome": r[2],
            "approval_id": r[3],
            "package_version": r[4],
            "rule_ids": r[5],
            "at": r[6].isoformat(),
        }
        for r in rows
    ]


def _records(conn: psycopg.Connection, case_id: str) -> list[dict]:
    records = []
    for store in MOCK_STORES:
        rows = conn.execute(
            psycopg.sql.SQL(
                "SELECT approval_id, data, created_at FROM mocks.{} WHERE case_id = %s"
            ).format(psycopg.sql.Identifier(store)),
            (case_id,),
        ).fetchall()
        records += [
            {"system": store, "approval_id": a, "data": d, "at": t.isoformat()}
            for a, d, t in rows
        ]
    return records
