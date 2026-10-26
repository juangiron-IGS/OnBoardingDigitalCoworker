"""MCP tool signatures shared by lane A (governance) and lane B (agents, connectors).

Changing this file needs an approval from someone in each lane.
"""

from datetime import date
from typing import Protocol, runtime_checkable

# The only actions the JobDiva and Workflow server may apply, all on mock stores.
SIMULATED_ACTIONS = frozenset(
    {"create_jobdiva_case", "create_task_list", "create_it_request"}
)


def idempotency_key(approval_id: str, action: str) -> str:
    """Key of one simulated action, so a retry never repeats it (NFR-REL-005)."""
    return f"{approval_id}:{action}"


@runtime_checkable
class JobDivaRead(Protocol):
    """The JobDiva READ server. Reads only, in mock and sandbox mode (BR-014)."""

    def read_start(self, start_id: str) -> dict: ...

    def read_start_notes(self, start_id: str) -> dict: ...

    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        """Return {"found": bool, "start_id": str | None}."""
        ...


@runtime_checkable
class JobDivaWorkflow(Protocol):
    """The JobDiva and Workflow server: the only server with write tools."""

    def execute_simulated_action(
        self, approval_id: str, package_version: int, action: str, payload: dict
    ) -> dict:
        """Apply one action from SIMULATED_ACTIONS after re-verifying the approval.

        Return {"status": "completed" | "already_completed", "key": str}.
        """
        ...


@runtime_checkable
class Mailbox(Protocol):
    """The Outlook mock: synthetic start emails."""

    def list_messages(self) -> list[dict]: ...

    def read_message(self, message_id: str) -> dict: ...


@runtime_checkable
class Alerts(Protocol):
    """The Teams mock: posts to the simulated alerts view."""

    def post_alert(self, case_id: str, recipient: str, text: str) -> dict: ...
