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
    for var in (
        "JOBDIVA_MOCK_URL",
        "JOBDIVA_WORKFLOW_URL",
        "TEAMS_MOCK_URL",
        "KNOWLEDGE_BASE_MOCK_URL",
        "COWORKER_MCP_URL",
    ):
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


_NEW_START = """Hi team, new start below.

Candidate ID: SYN-0077
Position: QA Engineer
Hiring manager: Lee Example
Start date: 2026-12-07
Client: Acme Synthetic
Client type: Enterprise
Division: Digital
Line of business: Professional Services
Employment type: W-2
Vendor company: INSPYR Solutions
Work arrangement: Hybrid
Pay rate: 40.00 USD/h
Work city: Los Angeles
Work state: CA
FLSA: Non-exempt
Billing contact: billing.acme@example.com
Equipment: Standard laptop, INSPYR
Sponsorship: No
"""


def test_new_email_arrives_and_the_coworker_processes_it(client) -> None:
    response = client.post(
        "/api/inbox",
        json={
            "sender": "recruiter.sam@example.com",
            "subject": "New start - SYN-0077 - QA Engineer",
            "body": _NEW_START,
        },
        headers=_as("recruiter"),
    )

    listed = client.get("/api/inbox", headers=_as("recruiter")).json()[0]
    assert response.status_code == 200
    assert response.json()["state"] == "needs_clarification"
    assert listed["subject"] == "New start - SYN-0077 - QA Engineer"
    assert listed["case_id"] == response.json()["case_id"]


@pytest.mark.parametrize(
    "bad",
    [
        {"sender": "not-an-email", "subject": "s", "body": "Candidate ID: X"},
        {"sender": "a@example.com", "subject": "", "body": "Candidate ID: X"},
        {"sender": "a@example.com", "subject": "s", "body": ""},
    ],
)
def test_new_email_with_bad_fields_is_refused(client, bad) -> None:
    response = client.post("/api/inbox", json=bad, headers=_as("recruiter"))

    assert response.status_code == 400


def test_claude_engine_without_a_key_is_a_clear_503(client, monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "claude")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.post(
        "/api/chat", json={"message": "hello"}, headers=_as("recruiter")
    )

    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_onboarding_team_records_hr_answer(client) -> None:
    # US-027, through the API
    case_id = _process(client, "05_flsa_conflict")["case_id"]

    refused = client.post(
        f"/api/cases/{case_id}/hr-answer",
        json={"field": "flsa", "value": "Exempt"},
        headers=_as("recruiter"),
    )
    recorded = client.post(
        f"/api/cases/{case_id}/hr-answer",
        json={"field": "flsa", "value": "Exempt"},
        headers=_as("onboarding"),
    )

    assert refused.status_code == 403
    assert recorded.json() == {"state": "ready_for_review", "package_version": 2}


def test_onboarding_team_changes_the_paperwork(client) -> None:
    # US-026, through the API
    case_id = _process(client, "01_complete_and_consistent")["case_id"]
    body = {"field": "paperwork", "action": "change", "values": ["Client NDA"]}

    refused = client.post(
        f"/api/cases/{case_id}/recommendation", json=body, headers=_as("recruiter")
    )
    changed = client.post(
        f"/api/cases/{case_id}/recommendation", json=body, headers=_as("onboarding")
    )

    assert refused.status_code == 403
    assert changed.json() == {"state": "ready_for_review", "package_version": 2}


def test_chat_answers_a_process_question_from_knowledge(client) -> None:
    response = client.post(
        "/api/chat",
        json={"message": "How do I request a laptop for a new hire?"},
        headers=_as("recruiter"),
    )

    assert response.status_code == 200
    assert "Source: KB-003" in response.json()["reply"]


def test_chat_with_a_case_still_answers_status(client) -> None:
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    reply = client.post(
        "/api/chat",
        json={"message": "How is it going?", "case_id": case_id},
        headers=_as("recruiter"),
    ).json()["reply"]

    assert "Ready for review" in reply


def test_knowledge_view_lists_records_and_pending_questions(client) -> None:
    asked = client.post(
        "/api/knowledge/ask",
        json={"question": "Which forms does a hire in Ohio need?"},
        headers=_as("recruiter"),
    ).json()

    view = client.get("/api/knowledge", headers=_as("recruiter")).json()

    assert asked["status"] == "no_answer"
    assert {r["id"] for r in view["records"]} >= {"KB-001", "KB-005"}
    assert view["pending"][0]["id"] == asked["pending_id"]


def test_only_the_onboarding_team_validates_knowledge(client) -> None:
    refused = client.post(
        "/api/knowledge/KB-005/validation",
        json={"decision": "validated"},
        headers=_as("recruiter"),
    )
    validated = client.post(
        "/api/knowledge/KB-005/validation",
        json={"decision": "validated"},
        headers=_as("onboarding"),
    )
    unknown = client.post(
        "/api/knowledge/KB-999/validation",
        json={"decision": "validated"},
        headers=_as("onboarding"),
    )
    bad = client.post(
        "/api/knowledge/KB-005/validation",
        json={"decision": "maybe"},
        headers=_as("onboarding"),
    )

    assert refused.status_code == 403
    assert validated.json() == {"record_id": "KB-005", "status": "validated"}
    assert unknown.status_code == 404
    assert bad.status_code == 400


def test_a_question_is_never_stored_as_a_case_answer(client) -> None:
    case_id = _process(client, "02_missing_two_fields")["case_id"]

    knowledge = client.post(
        "/api/chat",
        json={
            "message": "Which forms does a W-2 hire in Texas need?",
            "case_id": case_id,
        },
        headers=_as("recruiter"),
    ).json()
    status = client.post(
        "/api/chat",
        json={"message": "How is it going?", "case_id": case_id},
        headers=_as("recruiter"),
    ).json()
    questions = client.get(f"/api/cases/{case_id}", headers=_as("recruiter")).json()

    assert "Source: KB-001" in knowledge["reply"]
    assert "Needs clarification" in status["reply"]
    assert len(questions["questions"]) == 2


@pytest.mark.parametrize(
    ("path", "role", "body"),
    [
        ("it-approval", "it", {"package_version": 1}),
        ("recommendation", "onboarding", {"field": "path", "action": "confirm"}),
        ("decision", "approver", {"package_version": 1, "decision": "approve"}),
        ("hr-answer", "onboarding", {"field": "flsa", "value": "Exempt"}),
    ],
)
def test_unknown_case_is_a_404_not_a_500(client, path, role, body) -> None:
    response = client.post(
        f"/api/cases/case-000000000000/{path}", json=body, headers=_as(role)
    )

    assert response.status_code == 404


def test_new_email_with_an_unreadable_date_asks_the_sender(client) -> None:
    response = client.post(
        "/api/inbox",
        json={
            "sender": "recruiter@example.com",
            "subject": "Start",
            "body": "Candidate ID: SYN-7777\nStart date: 11/02/2026",
        },
        headers=_as("recruiter"),
    )

    assert response.status_code == 200
    assert response.json()["state"] == "needs_sender"


def test_hr_answer_must_be_a_known_value(client) -> None:
    case_id = _process(client, "05_flsa_conflict")["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/hr-answer",
        json={"field": "flsa", "value": "banana"},
        headers=_as("onboarding"),
    )

    assert response.status_code == 400


def test_hr_answer_on_a_rejected_case_writes_nothing(client, app_conn) -> None:
    case_id = _process(client, "05_flsa_conflict")["case_id"]
    client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": 1, "decision": "reject"},
        headers=_as("approver"),
    )

    response = client.post(
        f"/api/cases/{case_id}/hr-answer",
        json={"field": "flsa", "value": "Exempt"},
        headers=_as("onboarding"),
    )

    data = app_conn.execute(
        "SELECT data FROM cases WHERE id = %s", (case_id,)
    ).fetchone()[0]
    refused = app_conn.execute(
        "SELECT count(*) FROM audit_log WHERE case_id = %s"
        " AND action = 'record_hr_answer' AND outcome = 'refused'",
        (case_id,),
    ).fetchone()[0]
    assert response.status_code == 409
    assert "HR" not in data.get("answered_by", {}).values()
    assert refused == 1


def test_documents_and_payroll_through_the_api(client, monkeypatch) -> None:
    # US-022..024 end to end through the API, as in the demo
    monkeypatch.setenv("FEATURE_CANDIDATE_FOLLOWUP", "true")
    monkeypatch.setenv("FEATURE_PAYROLL_PACKAGE", "true")
    case_id = _process(client, "01_complete_and_consistent")["case_id"]
    client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": 1, "decision": "approve"},
        headers=_as("approver"),
    )
    view = client.get(f"/api/cases/{case_id}", headers=_as("onboarding")).json()
    items = [c["item"] for c in view["checklist"]]

    refused = client.post(
        f"/api/cases/{case_id}/followup/run",
        json={"at_hours": 24},
        headers=_as("recruiter"),
    )
    reminded = client.post(
        f"/api/cases/{case_id}/followup/run",
        json={"at_hours": 24},
        headers=_as("onboarding"),
    ).json()
    delivered = client.post(
        f"/api/cases/{case_id}/documents",
        json={"items": items},
        headers=_as("onboarding"),
    ).json()
    for item in items:
        client.post(
            f"/api/cases/{case_id}/documents/countersign",
            json={"item": item},
            headers=_as("onboarding"),
        )
    sent = client.post(
        f"/api/cases/{case_id}/payroll-handoff",
        json={"package_version": 1},
        headers=_as("onboarding"),
    ).json()
    task = client.post(
        f"/api/cases/{case_id}/payroll-returns",
        json={"issue": "Bank account mismatch"},
        headers=_as("onboarding"),
    )

    assert view["case"]["state"] == "documents_pending"
    assert refused.status_code == 403
    assert reminded == {"sent": [{"kind": "reminder", "at_hours": 24}]}
    assert delivered == {"state": "in_verification", "missing": []}
    assert sent["state"] == "sent_to_payroll"
    assert task.status_code == 200


def _dashboard_case(client, role: str, case_id: str) -> tuple[str, dict]:
    columns = client.get("/api/cases/dashboard", headers=_as(role)).json()
    for column in columns:
        for item in column["cases"]:
            if item["id"] == case_id:
                return column["state"], item
    raise AssertionError(f"{case_id} is not on the dashboard")


def test_dashboard_shows_each_case_under_its_state(client) -> None:
    # US-030 AC-001
    waiting = _process(client, "02_missing_two_fields")["case_id"]
    ready = _process(client, "01_complete_and_consistent")["case_id"]
    blocked = _process(client, "05_flsa_conflict")["case_id"]

    state, waiting_item = _dashboard_case(client, "onboarding", waiting)
    ready_state, ready_item = _dashboard_case(client, "onboarding", ready)
    _, blocked_item = _dashboard_case(client, "onboarding", blocked)

    assert state == "needs_clarification"
    assert waiting_item["pending"][0].startswith("Recruiter to answer: Bill rate")
    assert ready_state == "ready_for_review"
    assert "Approver to decide on package v1" in ready_item["pending"]
    assert any(r.startswith("Package blocked") for r in blocked_item["risks"])


def test_dashboard_never_shows_restricted_values(client) -> None:
    blocked = _process(client, "05_flsa_conflict")["case_id"]

    _, item = _dashboard_case(client, "it", blocked)

    text = " ".join(item["pending"] + item["risks"]).lower()
    assert "exempt" not in text


def test_info_package_through_the_api(client) -> None:
    # US-031 through the API: only the Onboarding Team prepares and sends it
    case_id = _process(client, "01_complete_and_consistent")["case_id"]
    client.post(
        f"/api/cases/{case_id}/decision",
        json={"package_version": 1, "decision": "approve"},
        headers=_as("approver"),
    )

    refused = client.post(f"/api/cases/{case_id}/info-package", headers=_as("it"))
    prepared = client.post(
        f"/api/cases/{case_id}/info-package", headers=_as("onboarding")
    ).json()
    sent = client.post(
        f"/api/cases/{case_id}/info-package/send", headers=_as("onboarding")
    ).json()

    assert refused.status_code == 403
    assert len(prepared["content"]["sections"]) == 3
    assert sent == {"status": "sent", "sections": 3}


def test_package_lists_client_forms_with_their_rule(client) -> None:
    # US-007 AC-002: forms by client, each with the rule that required it
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    lines = client.get(f"/api/cases/{case_id}", headers=_as("onboarding")).json()[
        "package"
    ]["lines"]

    assert {
        "field": "paperwork",
        "value": "Acme Synthetic confidentiality agreement",
        "label": "recommended",
        "source_or_rule_id": "R-PA-10",
    } in lines


def test_a_cited_rule_shows_its_owner_and_version(client) -> None:
    # US-007 AC-003
    rule = client.get("/api/rules/R-PA-10", headers=_as("onboarding")).json()
    unknown = client.get("/api/rules/R-PA-99", headers=_as("onboarding"))

    assert (rule["owner"], rule["version"], rule["status"]) == (
        "Onboarding",
        1,
        "draft",
    )
    assert rule["when"] == {"client": "Acme Synthetic"}
    assert unknown.status_code == 404


@pytest.mark.parametrize("role", ["recruiter", "it", "ldc"])
def test_a_form_named_after_the_flsa_status_is_hidden(client, role) -> None:
    # BR-011: "Non-exempt employee agreement" and its rule R-PA-05 reveal FLSA
    case_id = _process(client, "01_complete_and_consistent")["case_id"]

    lines = client.get(f"/api/cases/{case_id}", headers=_as(role)).json()["package"][
        "lines"
    ]
    approver = client.get(f"/api/cases/{case_id}", headers=_as("approver")).json()

    text = " ".join(f"{line['value']} {line['source_or_rule_id']}" for line in lines)
    assert "exempt" not in text.lower()
    assert "R-PA-05" not in text
    assert any(
        line["source_or_rule_id"] == "R-PA-05" for line in approver["package"]["lines"]
    )
