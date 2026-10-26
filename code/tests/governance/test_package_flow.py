import pytest

from services.case_service.application.build_package import build_package
from services.case_service.application.decisions import (
    record_approval,
    reject_case,
    return_package,
)
from services.case_service.application.move_case import move_case
from services.case_service.domain.case import CaseState
from services.case_service.domain.errors import GovernanceError

pytestmark = pytest.mark.db


def test_transition_is_audited_with_agent(app_conn, repo, audit, case_set_up) -> None:
    # US-036 AC-003: a transition is logged with the agent and the date
    entry = app_conn.execute(
        "SELECT agent, data_refs, recorded_at FROM audit_log"
        " WHERE case_id = %s AND action = 'transition' ORDER BY id DESC LIMIT 1",
        (case_set_up,),
    ).fetchone()
    assert entry[0] == "policy_case_setup"
    assert entry[1] == {"from": "validated", "to": "case_set_up"}
    assert entry[2] is not None


def test_no_package_for_failing_case(repo, audit, case_set_up, lines) -> None:
    # US-011 AC-003: a case that fails the checks gets no package
    move_case(repo, audit, case_set_up, CaseState.READY_FOR_REVIEW, agent="x")
    move_case(repo, audit, case_set_up, CaseState.APPROVAL_GATE, agent="x")
    move_case(repo, audit, case_set_up, CaseState.VALIDATED, agent="x")
    move_case(repo, audit, case_set_up, CaseState.NEEDS_CLARIFICATION, agent="x")

    with pytest.raises(GovernanceError) as refusal:
        build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    assert refusal.value.reason == "case_not_ready"


def test_package_built_and_case_ready_for_review(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # US-011 AC-001
    version = build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    state, current = app_conn.execute(
        "SELECT state, current_package_version FROM cases WHERE id = %s",
        (case_set_up,),
    ).fetchone()
    stored = app_conn.execute(
        "SELECT field, label, source_or_rule_id FROM package_lines"
        " WHERE case_id = %s AND version = %s ORDER BY id",
        (case_set_up, version),
    ).fetchall()
    assert (version, state, current) == (1, "ready_for_review", 1)
    assert stored == [
        ("work_state", "source", "jobdiva"),
        ("paperwork", "recommended", "R-PA-02"),
    ]


def test_change_creates_new_version_and_keeps_old(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # US-012 AC-002: a returned and corrected package gets a new version
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")
    return_package(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )
    move_case(repo, audit, case_set_up, CaseState.CASE_SET_UP, agent="orchestrator")

    version = build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    versions = app_conn.execute(
        "SELECT version FROM package_versions WHERE case_id = %s ORDER BY version",
        (case_set_up,),
    ).fetchall()
    assert version == 2
    assert versions == [(1,), (2,)]


def test_approval_records_approver_time_version_and_id(
    app_conn, repo, audit, case_set_up, lines
) -> None:
    # US-014 AC-001
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    approval_id = record_approval(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )

    entry = app_conn.execute(
        "SELECT agent, outcome, approval_id, package_version, recorded_at"
        " FROM audit_log WHERE case_id = %s AND action = 'approve_package'",
        (case_set_up,),
    ).fetchone()
    state = app_conn.execute(
        "SELECT state FROM cases WHERE id = %s", (case_set_up,)
    ).fetchone()[0]
    assert approval_id.startswith("apr-")
    assert entry[:4] == ("approver", "completed", approval_id, 1)
    assert entry[4] is not None
    assert state == "approved"


@pytest.mark.parametrize(
    ("decide", "action"),
    [(return_package, "return_package"), (reject_case, "reject_case")],
)
def test_return_or_reject_issues_no_approval_id(
    app_conn, repo, audit, case_set_up, lines, decide, action
) -> None:
    # US-014 AC-002
    build_package(repo, audit, case_set_up, lines, agent="orchestrator")

    decide(
        repo, audit, case_id=case_set_up, package_version=1, approver_role="approver"
    )

    decision = app_conn.execute(
        "SELECT approval_id FROM approvals WHERE case_id = %s", (case_set_up,)
    ).fetchone()[0]
    entry = app_conn.execute(
        "SELECT agent, approval_id, package_version FROM audit_log"
        " WHERE case_id = %s AND action = %s",
        (case_set_up, action),
    ).fetchone()
    assert decision is None
    assert entry == ("approver", None, 1)


def test_blocked_package_cannot_be_approved(repo, audit, case_set_up, lines) -> None:
    # US-033: an escalated conflict blocks the package
    build_package(repo, audit, case_set_up, lines, agent="orchestrator", escalated=True)

    with pytest.raises(GovernanceError) as refusal:
        record_approval(
            repo,
            audit,
            case_id=case_set_up,
            package_version=1,
            approver_role="approver",
        )
    assert refusal.value.reason == "package_not_ready"
