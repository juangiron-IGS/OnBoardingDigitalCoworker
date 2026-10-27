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


# Package data Payroll needs; equipment and bill-back lines stay with IT and finance.
PAYROLL_FIELDS = [
    "client",
    "role",
    "start_date",
    "employment_type",
    "work_city",
    "work_state",
    "flsa",
    "owner",
]
VALIDATED_LABELS = ("source", "recommended")


def payroll_package(lines: list[dict], checklist: list[dict]) -> dict[str, str]:
    """US-024 AC-001: only validated data of the approved package (source or
    recommended lines, never inferred or exception) and the verified documents."""
    payload: dict[str, str] = {}
    for line in lines:
        if line["field"] in PAYROLL_FIELDS and line["label"] in VALIDATED_LABELS:
            payload.setdefault(line["field"], line["value"])
    payload["verified_documents"] = "; ".join(
        c["item"] for c in checklist if c["status"] == "verified"
    )
    return payload


def send_payroll_package(
    workflow: JobDivaWorkflow,
    *,
    approval_id: str,
    package_version: int,
    payload: dict[str, str],
) -> dict:
    """Paychex (simulated), once the Onboarding Team approved the handoff."""
    return workflow.execute_simulated_action(
        approval_id, package_version, "send_payroll_package", payload
    )
