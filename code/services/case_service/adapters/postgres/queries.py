"""Read model for the web views: cases, their current package, audit trail and the
records the single writer created. Read only."""

from typing import Any

import psycopg

MOCK_STORES = ("jobdiva_cases", "task_lists", "it_requests")


def list_cases(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, person_ref, start_date, state, current_package_version, created_at"
        " FROM cases ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    return [
        {
            "id": r[0],
            "person_ref": r[1],
            "start_date": r[2].isoformat(),
            "state": r[3],
            "package_version": r[4],
            "created_at": r[5].isoformat(),
        }
        for r in rows
    ]


def case_detail(conn: psycopg.Connection, case_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, person_ref, start_date, state, current_package_version, data"
        " FROM cases WHERE id = %s",
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
    }
    return {
        "case": case,
        "package": _package(conn, case_id, row[4]),
        "audit": _audit(conn, case_id),
        "records": _records(conn, case_id),
    }


def _package(conn: psycopg.Connection, case_id: str, version: int) -> dict | None:
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
