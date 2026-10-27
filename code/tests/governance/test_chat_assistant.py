"""The chat converses through Claude for anything it does not route itself, using
only read-only tools; it never acts, and restricted data never reaches the model.
A scripted fake stands in for Claude: these tests never call the API."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.common.claude_client import ClaudeModelClient
from agents.common.model_client import RulesModelClient, load_labels
from agents.common.usage_meter import UsageMeter
from agents.orchestrator.assistant import TOOLS
from agents.orchestrator.orchestrator import Orchestrator
from mcp_servers.jobdiva_workflow.service import WorkflowService
from mcp_servers.mocks.knowledge.service import KnowledgeService
from mcp_servers.mocks.outlook.service import MailboxService
from mcp_servers.mocks.teams.service import AlertsService
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.service import LocalCaseService

pytestmark = pytest.mark.db

MAILBOX = MailboxService(
    Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"
)


class NoJobDivaDuplicates:
    def search_duplicate(self, person_ref, start_date) -> dict:
        return {"found": False, "start_id": None}


def _text(text: str):
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def _tool(name: str, args: dict):
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[SimpleNamespace(type="tool_use", id="t1", name=name, input=args)],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


class ScriptedClaude:
    """Returns the scripted responses in order and records every request."""

    def __init__(self, *responses) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **request):
        if "tools" not in request:  # field reading or record choice, not the chat
            return _structured(request)
        self.calls.append(request)
        return self.responses.pop(0)


def _structured(request: dict):
    """Field reading finds nothing new; record choice picks KB-004 for its question."""
    import json

    schema = request["output_config"]["format"]["schema"]["properties"]
    if "record_id" in schema:
        asked = request["messages"][0]["content"]
        data = {
            "record_id": "KB-004" if "approves" in asked.split("<question>")[1] else ""
        }
    else:
        data = {"values": {}, "ambiguous": []}
    return _text(json.dumps(data))


def _coworker(app_conn, messages) -> Orchestrator:
    model = (
        ClaudeModelClient(
            load_labels(),
            UsageMeter(cap_per_run=50),
            client=SimpleNamespace(messages=messages),
            model="claude-haiku-5-5",
        )
        if messages
        else RulesModelClient(load_labels(), UsageMeter(cap_per_run=50))
    )
    return Orchestrator(
        cases=LocalCaseService(app_conn, NoJobDivaDuplicates()),
        model=model,
        catalog=RulesCatalog.load(),
        alerts=AlertsService(app_conn),
        workflow=WorkflowService(app_conn),
        knowledge=KnowledgeService(app_conn),
    )


def _start(coworker) -> str:
    message = MAILBOX.read_message("02_missing_two_fields")
    return coworker.process_start(message["body"], source=message["from"]).case_id


def test_claude_answers_from_the_tools(app_conn) -> None:
    claude = ScriptedClaude(
        _tool("my_cases", {}), _text("Tienes 1 caso: SYN-0043 espera Bill rate.")
    )
    coworker = _coworker(app_conn, claude)
    _start(coworker)

    reply = coworker.chat("¿Qué casos tengo pendientes?", asked_by="recruiter")

    tool_result = claude.calls[1]["messages"][-1]["content"][0]["content"]
    assert reply.reply == "Tienes 1 caso: SYN-0043 espera Bill rate."
    assert "SYN-0043" in tool_result and "Bill rate" in tool_result
    audit = app_conn.execute(
        "SELECT data_refs FROM audit_log WHERE action = 'assistant_reply'"
        " ORDER BY id DESC LIMIT 1"
    ).fetchone()[0]
    assert audit == {"tools": "my_cases", "asked_by": "recruiter"}


def test_the_tools_only_read() -> None:
    names = {tool["name"] for tool in TOOLS}

    assert names == {
        "my_cases",
        "case_status",
        "open_questions",
        "ask_onboarding_knowledge",
    }
    for word in ("approve", "reject", "return", "assign", "execute", "send"):
        assert not any(word in name for name in names)


def test_a_known_process_question_is_answered_by_its_record(app_conn) -> None:
    claude = ScriptedClaude(_text("unused"))
    coworker = _coworker(app_conn, claude)

    reply = coworker.chat("Who approves the onboarding package?", asked_by="recruiter")

    assert "Source: KB-004" in reply.reply
    assert all("tools" not in call for call in claude.calls)  # no conversation


def test_restricted_sentences_never_reach_claude() -> None:
    # Defense in depth: converse itself drops them, whatever routed the message
    claude = ScriptedClaude(_text("Entendido."))
    engine = ClaudeModelClient(
        load_labels(),
        UsageMeter(cap_per_run=50),
        client=SimpleNamespace(messages=claude),
        model="claude-haiku-5-5",
    )

    engine.converse(
        "system",
        "Hola. El candidato es non-exempt y tiene visa H-1B.",
        TOOLS,
        lambda name, args: "{}",
        run_id="r1",
    )

    sent = claude.calls[-1]["messages"][0]["content"]
    assert "Hola." in sent
    assert "exempt" not in sent.lower() and "visa" not in sent.lower()


def test_an_answer_to_a_case_question_is_still_stored(app_conn) -> None:
    claude = ScriptedClaude(_text("unused"))
    coworker = _coworker(app_conn, claude)
    case_id = _start(coworker)

    coworker.chat("61.00 USD/h", case_id=case_id, asked_by="recruiter")

    assert coworker.cases.case_data(case_id)["bill_rate"] == "61.00 USD/h"
    assert all("tools" not in call for call in claude.calls)


def test_without_claude_the_chat_keeps_its_help(app_conn) -> None:
    coworker = _coworker(app_conn, None)

    reply = coworker.chat("hola", asked_by="recruiter")

    assert reply.reply.startswith("I can start an onboarding case")


def test_a_claude_failure_falls_back_to_the_help(app_conn) -> None:
    import anthropic
    import httpx

    class Failing:
        def create(self, **request):
            raise anthropic.APIConnectionError(
                request=httpx.Request("POST", "https://api.anthropic.com")
            )

    coworker = _coworker(app_conn, Failing())

    reply = coworker.chat("hola", asked_by="recruiter")

    assert reply.reply.startswith("I can start an onboarding case")


def test_an_flsa_question_goes_to_hr_without_claude(app_conn) -> None:
    claude = ScriptedClaude(_text("unused"))
    coworker = _coworker(app_conn, claude)

    reply = coworker.chat("Is SYN-1243 exempt?", asked_by="it")

    assert "HR decides them" in reply.reply
    assert claude.calls == []
