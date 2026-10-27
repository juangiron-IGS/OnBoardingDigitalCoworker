"""The MCP contracts (contracts/mcp_tools.py) implemented over MCP tool calls."""

from datetime import date

from services.case_service.domain.errors import ApprovalRefused, GovernanceError

from .mcp_client import McpToolClient

_APPROVAL_REASONS = frozenset({"no_approval", "version_mismatch", "case_not_approved"})


def _refusal(result: dict) -> GovernanceError | None:
    """A refusal crosses MCP as data, so its reason is kept (BR-002)."""
    if isinstance(result, dict) and result.get("status") == "refused":
        reason = str(result.get("reason") or "refused")
        return (
            ApprovalRefused(reason)
            if reason in _APPROVAL_REASONS
            else GovernanceError(reason)
        )
    return None


class McpJobDivaWorkflow:
    def __init__(self, client: McpToolClient) -> None:
        self._client = client

    def execute_simulated_action(
        self, approval_id: str, package_version: int, action: str, payload: dict
    ) -> dict:
        result = self._client.call(
            "execute_simulated_action",
            {
                "approval_id": approval_id,
                "package_version": package_version,
                "action": action,
                "payload": payload,
            },
        )
        refusal = _refusal(result)
        if refusal:
            raise refusal
        return result


class McpJobDivaRead:
    def __init__(self, client: McpToolClient) -> None:
        self._client = client

    def read_start(self, start_id: str) -> dict:
        return self._client.call("read_start", {"start_id": start_id})

    def read_start_notes(self, start_id: str) -> dict:
        return self._client.call("read_start_notes", {"start_id": start_id})

    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        return self._client.call(
            "search_duplicate",
            {"person_ref": person_ref, "start_date": start_date.isoformat()},
        )


class McpAlerts:
    def __init__(self, client: McpToolClient) -> None:
        self._client = client

    def post_alert(self, case_id: str, recipient: str, text: str) -> dict:
        return self._client.call(
            "post_alert", {"case_id": case_id, "recipient": recipient, "text": text}
        )


class McpKnowledge:
    def __init__(self, client: McpToolClient) -> None:
        self._client = client

    def records(self) -> list[dict]:
        return self._client.call("list_records", {})

    def validate(self, record_id: str, decision: str, *, decided_by: str) -> str:
        result = self._client.call(
            "validate_record",
            {"record_id": record_id, "decision": decision, "decided_by": decided_by},
        )
        if result.get("status") == "refused":
            if result.get("reason") == "unknown_record":
                raise KeyError(record_id)
            raise ValueError(result.get("reason"))
        return result["status"]

    def register_unresolved(
        self, question: str, *, asked_by: str, channel: str, reason: str
    ) -> str:
        return self._client.call(
            "register_unresolved",
            {
                "question": question,
                "asked_by": asked_by,
                "channel": channel,
                "reason": reason,
            },
        )

    def log_answer(
        self, record_id: str, status: str, *, channel: str, matched_by: str = "words"
    ) -> None:
        self._client.call(
            "log_answer",
            {
                "record_id": record_id,
                "status": status,
                "channel": channel,
                "matched_by": matched_by,
            },
        )

    def pending(self) -> list[dict]:
        return self._client.call("pending_questions", {})
