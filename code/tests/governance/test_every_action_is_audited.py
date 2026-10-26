import psycopg
import pytest

from services.case_service.adapters.postgres.audit_log import PostgresAuditLog

pytestmark = pytest.mark.db


def _rows(conn: psycopg.Connection, case_id: str) -> list[tuple]:
    return conn.execute(
        "SELECT agent, action, outcome, approval_id, package_version, rule_ids,"
        " data_refs FROM audit_log WHERE case_id = %s ORDER BY id",
        (case_id,),
    ).fetchall()


def test_completed_action_has_agent_rules_and_data(app_conn, case_id) -> None:
    # US-018 AC-001: action, agent, case, date, data and rule IDs used
    audit = PostgresAuditLog(app_conn)

    audit.append(
        case_id=case_id,
        agent="policy_case_setup",
        action="recommend_paperwork",
        outcome="completed",
        rule_ids=["R-PA-02"],
        data_refs={"work_state": "jobdiva", "contract_type": "jobdiva"},
    )

    rows = _rows(app_conn, case_id)
    assert rows == [
        (
            "policy_case_setup",
            "recommend_paperwork",
            "completed",
            None,
            None,
            ["R-PA-02"],
            {"work_state": "jobdiva", "contract_type": "jobdiva"},
        )
    ]


def test_refused_action_is_audited(app_conn, case_id) -> None:
    # US-018 AC-002: a refusal gets an entry with the same fields
    audit = PostgresAuditLog(app_conn)

    audit.append(
        case_id=case_id,
        agent="jobdiva_workflow",
        action="create_jobdiva_case",
        outcome="refused",
        approval_id="apr-1",
        package_version=1,
    )

    agent, action, outcome, approval_id, version, rule_ids, data_refs = _rows(
        app_conn, case_id
    )[0]
    assert (agent, action, outcome) == (
        "jobdiva_workflow",
        "create_jobdiva_case",
        "refused",
    )
    assert (approval_id, version) == ("apr-1", 1)
    assert rule_ids == [] and data_refs == {}


def test_unknown_outcome_is_rejected(app_conn, case_id) -> None:
    audit = PostgresAuditLog(app_conn)

    with pytest.raises(ValueError, match="outcome"):
        audit.append(case_id=case_id, agent="x", action="y", outcome="done")


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_log SET outcome = 'completed' WHERE case_id = %s",
        "DELETE FROM audit_log WHERE case_id = %s",
    ],
)
def test_app_role_cannot_change_audit_entries(app_conn, case_id, statement) -> None:
    # NFR-SEC-004: the audit log is append-only
    PostgresAuditLog(app_conn).append(
        case_id=case_id, agent="orchestrator", action="route", outcome="completed"
    )

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        app_conn.execute(statement, (case_id,))


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_log SET outcome = 'completed' WHERE case_id = %s",
        "DELETE FROM audit_log WHERE case_id = %s",
    ],
)
def test_audit_writer_role_is_insert_only(
    audit_writer_conn, case_id, statement
) -> None:
    PostgresAuditLog(audit_writer_conn).append(
        case_id=case_id, agent="orchestrator", action="route", outcome="completed"
    )

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        audit_writer_conn.execute(statement, (case_id,))
