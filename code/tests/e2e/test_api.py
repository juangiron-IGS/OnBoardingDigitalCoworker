import pytest
from fastapi.testclient import TestClient

from web.api.deps import get_conn
from web.api.main import app

pytestmark = pytest.mark.db


@pytest.fixture
def client(app_conn):
    app.dependency_overrides[get_conn] = lambda: app_conn
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _as(role: str) -> dict:
    return {"X-Role": role}


def _process(client, message_id: str) -> dict:
    response = client.post(f"/api/inbox/{message_id}/process", headers=_as("recruiter"))
    assert response.status_code == 200, response.text
    return response.json()


def test_inbox_lists_the_seed_emails(client) -> None:
    response = client.get("/api/inbox", headers=_as("recruiter"))

    assert response.status_code == 200
    assert "02_missing_two_fields" in [m["id"] for m in response.json()]


def test_processed_email_shows_its_case_and_package(client) -> None:
    started = _process(client, "01_complete_and_consistent")

    view = client.get(
        f"/api/cases/{started['case_id']}", headers=_as("approver")
    ).json()

    assert started["state"] == "ready_for_review"
    assert view["case"]["state"] == "ready_for_review"
    assert view["package"]["version"] == 1
    assert {"label", "source_or_rule_id"} <= set(view["package"]["lines"][0])
    assert any(entry["agent"] == "policy_case_setup" for entry in view["audit"])


def test_it_role_does_not_see_restricted_fields(client) -> None:
    # US-040 AC-001 / AC-002
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    it_view = client.get(f"/api/cases/{case_id}", headers=_as("it")).json()
    approver_view = client.get(f"/api/cases/{case_id}", headers=_as("approver")).json()

    def flsa(view):
        return next(
            line["value"]
            for line in view["package"]["lines"]
            if line["field"] == "flsa"
        )

    assert it_view["case"]["data"]["flsa"] == "Restricted"
    assert it_view["case"]["data"]["sponsorship_visa"] == "Restricted"
    assert flsa(it_view) == "Restricted"
    assert flsa(approver_view) == "Non-exempt"


def test_answers_complete_the_demo_case(client) -> None:
    case_id = _process(client, "02_missing_two_fields")["case_id"]

    client.post(
        f"/api/cases/{case_id}/answers",
        json={"field": "timesheet_approver", "value": "Lee Example"},
        headers=_as("recruiter"),
    )
    response = client.post(
        f"/api/cases/{case_id}/answers",
        json={"field": "bill_rate", "value": "61.00 USD/h"},
        headers=_as("recruiter"),
    )

    assert response.json()["state"] == "ready_for_review"


def test_approval_runs_the_actions(client) -> None:
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": 1, "decision": "approve"},
        headers=_as("approver"),
    )
    view = client.get(f"/api/cases/{case_id}", headers=_as("approver")).json()

    assert response.status_code == 200
    assert response.json()["state"] == "actions_executed"
    assert {r["system"] for r in view["records"]} == {"jobdiva_cases", "task_lists"}


def test_stale_version_returns_409_with_current_version(client) -> None:
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": 2, "decision": "approve"},
        headers=_as("approver"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "refused": "version_mismatch",
        "current_version": 1,
    }


def test_only_the_approver_can_decide(client) -> None:
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": 1, "decision": "approve"},
        headers=_as("recruiter"),
    )

    assert response.status_code == 403


def test_bad_input_returns_400_naming_the_field(client) -> None:
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": "one", "decision": "approve"},
        headers=_as("approver"),
    )

    assert response.status_code == 400
    assert "package_version" in response.text


def test_unknown_role_is_refused(client) -> None:
    assert client.get("/api/inbox", headers=_as("admin")).status_code == 400


def test_unknown_message_returns_404(client) -> None:
    response = client.post("/api/inbox/nope/process", headers=_as("recruiter"))

    assert response.status_code == 404


def test_path_traversal_reads_nothing(client) -> None:
    response = client.post("/api/inbox/../../.env/process", headers=_as("recruiter"))

    assert response.status_code in {404, 405}
    assert "DATABASE_URL" not in response.text


def test_case_view_lists_the_open_questions(client) -> None:
    case_id = _process(client, "02_missing_two_fields")["case_id"]

    view = client.get(f"/api/cases/{case_id}", headers=_as("recruiter")).json()

    assert view["questions"] == [
        {"field": "bill_rate", "label": "Bill rate", "kind": "missing"},
        {
            "field": "timesheet_approver",
            "label": "Timesheet approver",
            "kind": "missing",
        },
    ]


def test_chat_endpoint_starts_and_continues_a_case(client) -> None:
    start = "Candidate ID: SYN-0051\nStart date: 2026-11-30\nPosition: Analyst"

    first = client.post("/api/chat", json={"message": start}, headers=_as("recruiter"))
    reply = client.post(
        "/api/chat",
        json={"message": "Remote", "case_id": first.json()["case_id"]},
        headers=_as("recruiter"),
    )

    assert first.status_code == 200
    assert first.json()["asking"]
    assert reply.status_code == 200
    assert reply.json()["case_id"] == first.json()["case_id"]


def test_chat_endpoint_refuses_an_empty_message(client) -> None:
    response = client.post("/api/chat", json={"message": ""}, headers=_as("recruiter"))

    assert response.status_code == 400


def test_health_reports_the_database(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_health_reports_mcp_servers_that_are_down(client, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_TRANSPORT", "mcp")
    for var in ("JOBDIVA_MOCK_URL", "JOBDIVA_WORKFLOW_URL", "TEAMS_MOCK_URL"):
        monkeypatch.setenv(var, "http://127.0.0.1:9")

    body = client.get("/api/health").json()

    assert body["transport"] == "mcp"
    assert body["status"] == "degraded"
    assert set(body["mcp_servers"].values()) == {"down"}


def test_approver_assigns_the_follow_up_owner(client) -> None:
    # US-032 AC-002
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/owner",
        json={"owner": "Dana Synthetic"},
        headers=_as("approver"),
    )

    view = client.get(f"/api/cases/{case_id}", headers=_as("recruiter")).json()
    assert response.status_code == 200
    assert view["case"]["assigned_owner"] == "Dana Synthetic"


def test_only_the_approver_assigns_the_owner(client) -> None:
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/owner",
        json={"owner": "Dana Synthetic"},
        headers=_as("recruiter"),
    )

    assert response.status_code == 403


def test_case_reports_the_package_timing(client) -> None:
    # US-012 AC-001 and AC-003
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    listed = client.get("/api/cases", headers=_as("approver")).json()
    timing = next(c for c in listed if c["id"] == case_id)["package_timing"]

    assert timing["met"] is True
    assert timing["target_seconds"] == 300


def test_it_approves_the_laptop_request(client, monkeypatch) -> None:
    # US-020 AC-002, through the API
    monkeypatch.setenv("FEATURE_ACCESS_EQUIPMENT", "true")
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    refused = client.post(
        f"/api/cases/{case_id}/it-approval",
        json={"package_version": 1},
        headers=_as("recruiter"),
    )
    approved = client.post(
        f"/api/cases/{case_id}/it-approval",
        json={"package_version": 1},
        headers=_as("it"),
    )

    view = client.get(f"/api/cases/{case_id}", headers=_as("it")).json()
    assert refused.status_code == 403
    assert approved.json() == {"case_id": case_id, "it_approved": True, "sent": False}
    assert view["case"]["it_approved"] is True
