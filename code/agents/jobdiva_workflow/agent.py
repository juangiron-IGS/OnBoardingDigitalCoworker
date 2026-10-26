"""JobDiva and Workflow agent (Must): the only agent that calls write tools, and only
the JobDiva and Workflow server's, after approval (BR-002, US-034)."""

from contracts.mcp_tools import JobDivaWorkflow

AGENT = "jobdiva_workflow"

# Actions run after approval, in order. Payloads carry no restricted fields.
APPROVED_ACTIONS = ["create_jobdiva_case", "create_task_list"]
PAYLOAD_FIELDS = ["client", "role", "start_date", "work_arrangement"]


def send_it_request(
    workflow: JobDivaWorkflow,
    *,
    approval_id: str,
    package_version: int,
    payload: dict[str, str],
) -> dict:
    """The Chelsea Tech request, once the approver and IT approved (BR-012)."""
    return workflow.execute_simulated_action(
        approval_id, package_version, "create_it_request", payload
    )


def run_approved_actions(
    workflow: JobDivaWorkflow,
    *,
    approval_id: str,
    package_version: int,
    data: dict[str, object],
) -> list[dict]:
    payload = {field: str(data[field]) for field in PAYLOAD_FIELDS if data.get(field)}
    return [
        workflow.execute_simulated_action(approval_id, package_version, action, payload)
        for action in APPROVED_ACTIONS
    ]
