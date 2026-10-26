"""Onboarding Orchestrator: owns each case and routes it through the specialized
agents on one shared context (STACK-002, AC8)."""

import uuid
from dataclasses import dataclass, field
from datetime import date

from agents.common import notifications
from agents.common.model_client import ModelClient, load_labels, load_required
from agents.intake_validation import agent as intake
from agents.jobdiva_workflow import agent as workflow_agent
from agents.policy_case_setup import agent as policy
from contracts.case_service_api import CaseIntake, CaseServiceClient, CaseState
from contracts.mcp_tools import Alerts, JobDivaWorkflow
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.errors import DuplicateCase

from .chat import ChatReply

AGENT = "orchestrator"
RECRUITER = "Recruiter"


@dataclass(frozen=True)
class StartResult:
    state: str
    case_id: str | None = None
    missing: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    blocked_by: str | None = None


class Orchestrator:
    def __init__(
        self,
        *,
        cases: CaseServiceClient,
        model: ModelClient,
        catalog: RulesCatalog,
        alerts: Alerts,
        workflow: JobDivaWorkflow,
    ) -> None:
        self._cases = cases
        self._model = model
        self._catalog = catalog
        self._alerts = alerts
        self._workflow = workflow
        self._labels = load_labels()
        self._required = load_required()

    @property
    def cases(self) -> CaseServiceClient:
        return self._cases

    def chat(self, message: str, *, case_id: str | None = None) -> "ChatReply":
        """One chat message from the recruiter or the Onboarding Team."""
        from .chat import respond

        return respond(self, message, case_id)

    def read_labelled(self, text: str) -> dict[str, str]:
        """Fields stated in a message, through the metered model client."""
        extraction = self._model.extract_fields(
            text, list(self._labels), case_id="chat", run_id=uuid.uuid4().hex
        )
        return {k: v for k, v in extraction.values.items() if v is not None}

    def process_start(
        self, text: str, *, source: str, channel: str = "email"
    ) -> StartResult:
        """J1: a start email or chat message becomes a case (US-001, US-002)."""
        run_id = uuid.uuid4().hex
        reading = intake.read_start(
            text,
            model=self._model,
            fields=list(self._labels),
            required=self._required,
            case_id="new",
            run_id=run_id,
        )
        person, start = (
            reading.values.get("person_ref"),
            reading.values.get("start_date"),
        )
        if not person or not start:
            return StartResult(
                state="needs_sender", missing=["person_ref", "start_date"]
            )
        data = {
            **reading.values,
            "source": source,
            "source_channel": channel,
            "contradictions": reading.contradictions,
        }
        try:
            case_id = self._cases.create_case(
                CaseIntake(
                    person_ref=person, start_date=date.fromisoformat(start), data=data
                ),
                agent=intake.AGENT,
            )
        except DuplicateCase as blocked:
            notifications.notify(
                self._alerts,
                blocked.existing_ref,
                RECRUITER,
                notifications.duplicate_text(blocked.existing_ref),
            )
            return StartResult(
                state="blocked_duplicate", blocked_by=blocked.existing_ref
            )

        self._cases.move_case(case_id, CaseState.VALIDATED, agent=intake.AGENT)
        return self._evaluate(case_id)

    def answer(self, case_id: str, field_name: str, value: str) -> str:
        """The recruiter answers one question (US-003)."""
        if field_name not in self._labels:
            raise ValueError(f"unknown field {field_name!r}")
        data = self._cases.case_data(case_id)
        contradictions = [f for f in data.get("contradictions", []) if f != field_name]
        self._cases.record_answers(
            case_id,
            {field_name: value, "contradictions": contradictions},
            agent=RECRUITER.lower(),
            source="recruiter",
        )
        if self._cases.case_state(case_id) is CaseState.NEEDS_CLARIFICATION:
            pending = self._pending(self._cases.case_data(case_id))
            if not pending:
                self._cases.move_case(case_id, CaseState.VALIDATED, agent=intake.AGENT)
                return self._evaluate(case_id).state
        return self._cases.case_state(case_id).value

    def decide(
        self,
        case_id: str,
        *,
        package_version: int,
        decision: str,
        approver_role: str,
        comment: str | None = None,
    ) -> dict:
        """J2: the approver decides; approved actions run through the single writer."""
        if decision == "approve":
            approval_id = self._cases.record_approval(
                case_id,
                package_version=package_version,
                approver_role=approver_role,
                comment=comment,
            )
            results = workflow_agent.run_approved_actions(
                self._workflow,
                approval_id=approval_id,
                package_version=package_version,
                data=self._cases.case_data(case_id),
            )
            self._cases.move_case(case_id, CaseState.ACTIONS_EXECUTED, agent=AGENT)
            return {
                "state": self._cases.case_state(case_id).value,
                "approval_id": approval_id,
                "actions": results,
            }
        handler = {
            "return": self._cases.return_package,
            "reject": self._cases.reject_case,
        }
        if decision not in handler:
            raise ValueError(f"unknown decision {decision!r}")
        handler[decision](
            case_id,
            package_version=package_version,
            approver_role=approver_role,
            comment=comment,
        )
        return {"state": self._cases.case_state(case_id).value, "approval_id": None}

    def questions(self, case_id: str) -> list[dict]:
        """Open questions for the recruiter: missing fields and contradictions."""
        data = self._cases.case_data(case_id)
        contradictions = list(data.get("contradictions", []))
        missing = intake.missing_fields(data, self._required, contradictions)
        return [
            {"field": f, "label": notifications.label(f, self._labels), "kind": kind}
            for kind, fields in (
                ("missing", missing),
                ("contradiction", contradictions),
            )
            for f in fields
        ]

    def _pending(self, data: dict) -> list[str]:
        return intake.missing_fields(data, self._required) + list(
            data.get("contradictions", [])
        )

    def _evaluate(self, case_id: str) -> StartResult:
        data = self._cases.case_data(case_id)
        contradictions = list(data.get("contradictions", []))
        missing = intake.missing_fields(data, self._required, contradictions)
        if missing or contradictions:
            self._cases.move_case(
                case_id, CaseState.NEEDS_CLARIFICATION, agent=intake.AGENT
            )
            notifications.notify(
                self._alerts,
                case_id,
                RECRUITER,
                notifications.missing_fields_text(
                    case_id, missing, contradictions, self._labels
                ),
            )
            self._cases.log_action(
                case_id,
                agent=intake.AGENT,
                action="alert_recruiter",
                data_refs={f: "missing" for f in missing}
                | {f: "contradiction" for f in contradictions},
            )
            return StartResult(
                state=CaseState.NEEDS_CLARIFICATION.value,
                case_id=case_id,
                missing=missing,
                contradictions=contradictions,
            )

        self._cases.move_case(case_id, CaseState.CASE_SET_UP, agent=policy.AGENT)
        lines = policy.recommend(data, self._catalog)
        self._cases.build_package(case_id, lines, agent=policy.AGENT)
        return StartResult(state=self._cases.case_state(case_id).value, case_id=case_id)
