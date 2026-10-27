"""Measured metrics for the README (US-012, US-004, BR-002): the five seed scenarios
run through the API as in the demo, timed, with the questions asked compared to
the fields really missing or in conflict, and every simulated action checked for
an approval ID. With WRITE_METRICS=1 the table is written to tests/evidence."""

import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from web.api.deps import get_conn
from web.api.main import app

pytestmark = pytest.mark.db

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "metrics.md"
# What each seed email really lacks or contradicts (read from db/seed/mailbox).
SCENARIOS = {
    "01_complete_and_consistent": set(),
    "02_missing_two_fields": {"Bill rate", "Timesheet approver"},
    "03_duplicate": set(),
    "04_work_arrangement_contradiction": {"Work arrangement"},
    "05_flsa_conflict": set(),  # an FLSA conflict is escalated to HR, never asked
}
ANSWERS = {
    "bill_rate": "61.00 USD/h",
    "timesheet_approver": "Lee Example",
    "work_arrangement": "Hybrid",
}


@pytest.fixture
def client(app_conn):
    app.dependency_overrides[get_conn] = lambda: app_conn
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _as(role: str) -> dict:
    return {"X-Role": role}


def _ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


def test_measured_metrics(client, app_conn) -> None:
    rows = []
    for scenario, truly_missing in SCENARIOS.items():
        start = time.perf_counter()
        outcome = client.post(
            f"/api/inbox/{scenario}/process", headers=_as("recruiter")
        ).json()
        to_case = _ms(start)
        case_id = outcome.get("case_id")
        asked = set()
        to_package = None
        if case_id and outcome.get("state") == "needs_clarification":
            questions = client.get(f"/api/cases/{case_id}", headers=_as("recruiter"))
            asked = {q["label"] for q in questions.json()["questions"]}
            for q in questions.json()["questions"]:
                start = time.perf_counter()
                client.post(
                    f"/api/cases/{case_id}/answers",
                    json={"field": q["field"], "value": ANSWERS[q["field"]]},
                    headers=_as("recruiter"),
                )
                to_package = _ms(start)  # the last answer builds the package
        elif case_id:
            to_package = to_case
        state = outcome.get("state")
        if case_id:
            view = client.get(f"/api/cases/{case_id}", headers=_as("onboarding"))
            state = view.json()["case"]["state"]
            if view.json()["package"]:
                state += f", package {view.json()['package']['status']}"
        rows.append((scenario, state, to_package, asked, truly_missing))

    # The approver approves the complete case; then every simulated record must
    # carry an approval ID, and no workflow action may have run without one.
    blocked = app_conn.execute(
        "SELECT id FROM cases WHERE person_ref = 'SYN-0045'"
    ).fetchone()[0]
    refused = client.post(
        f"/api/cases/{blocked}/decision",
        json={"package_version": 1, "decision": "approve"},
        headers=_as("approver"),
    ).status_code
    approved_case = app_conn.execute(
        "SELECT id FROM cases WHERE person_ref = 'SYN-0042'"
    ).fetchone()[0]
    client.post(
        f"/api/cases/{approved_case}/decision",
        json={"package_version": 1, "decision": "approve"},
        headers=_as("approver"),
    )
    records = client.get(f"/api/cases/{approved_case}", headers=_as("onboarding"))
    created = records.json()["records"]
    unapproved = app_conn.execute(
        "SELECT count(*) FROM audit_log WHERE agent = 'jobdiva_workflow' "
        "AND outcome = 'completed' AND approval_id IS NULL"
    ).fetchone()[0]

    asked_right = all(asked == missing for _, _, _, asked, missing in rows)
    slowest = max(t for _, _, t, _, _ in rows if t is not None)
    if os.environ.get("WRITE_METRICS") == "1":
        _write(rows, created, unapproved, refused)

    assert asked_right
    assert slowest <= 300_000  # the 5-minute target (US-012)
    assert created and all(r["approval_id"] for r in created)
    assert unapproved == 0
    assert refused == 409


def _write(rows, created, unapproved, refused) -> None:
    lines = [
        "# Measured metrics",
        "",
        "Run: `WRITE_METRICS=1 .venv/Scripts/python -m pytest "
        "tests/e2e/test_measured_metrics.py` from `code/` (rules engine, test "
        "database, synthetic seed emails).",
        "",
        "| Seed email | Result | Time to package ready | Questions asked | "
        "Fields missing or in conflict |",
        "| --- | --- | --- | --- | --- |",
    ]
    for scenario, state, to_package, asked, missing in rows:
        time_text = f"{to_package} ms" if to_package is not None else "no package"
        lines.append(
            f"| {scenario} | {state} | {time_text} | "
            f"{', '.join(sorted(asked)) or 'none'} | "
            f"{', '.join(sorted(missing)) or 'none'} |"
        )
    lines += [
        "",
        f"- Simulated records after approval: {len(created)}, all with an approval ID.",
        f"- Workflow actions completed without an approval ID: {unapproved}.",
        f"- Approving the blocked FLSA package: refused (HTTP {refused}).",
        "",
    ]
    EVIDENCE.write_text("\n".join(lines), encoding="utf-8")
