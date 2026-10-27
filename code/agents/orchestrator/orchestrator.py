"""Onboarding Orchestrator: owns each case and routes it through the specialized
agents on one shared context (STACK-002, AC8)."""

import os
import uuid
from dataclasses import dataclass, field
from datetime import date

from agents.access_equipment import agent as access
from agents.candidate_followup import agent as followup_agent
from agents.common import notifications
from agents.common.model_client import ModelClient, load_labels, load_required
from agents.intake_validation import agent as intake
from agents.jobdiva_workflow import agent as workflow_agent
from agents.onboarding_knowledge import agent as knowledge_agent
from agents.policy_case_setup import agent as policy
from contracts.case_service_api import CaseIntake, CaseServiceClient, CaseState
from contracts.mcp_tools import Alerts, JobDivaRead, JobDivaWorkflow, KnowledgeBase
from services.case_service.adapters.rules_files.catalog import RulesCatalog
from services.case_service.domain.errors import (
    DuplicateCase,
    GovernanceError,
    InvalidTransition,
)
from services.case_service.domain.package import PackageLine

from .chat import ChatReply

AGENT = "orchestrator"
RECRUITER = "Recruiter"
SUPERVISOR = "Onboarding Supervisor"
IT = "IT"
CANDIDATE = "Candidate"
ONBOARDING = "Onboarding Team"


def _flag(name: str, value: bool | None) -> bool:
    if value is not None:
        return value
    return os.environ.get(name, "false").lower() == "true"


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
        jobdiva: JobDivaRead | None = None,
        access_equipment: bool | None = None,
        knowledge: KnowledgeBase | None = None,
        followup: bool | None = None,
        payroll: bool | None = None,
    ) -> None:
        self._cases = cases
        self._model = model
        self._catalog = catalog
        self._alerts = alerts
        self._workflow = workflow
        self._jobdiva = jobdiva
        self._knowledge = knowledge  # Should agent S3 (US-025)
        # Should agent S1, behind its feature flag (checkpoint scope priority)
        self._access = (
            os.environ.get("FEATURE_ACCESS_EQUIPMENT", "false").lower() == "true"
            if access_equipment is None
            else access_equipment
        )
        # Should agents S2 and S4 (US-022..024), behind their feature flags
        self._followup = _flag("FEATURE_CANDIDATE_FOLLOWUP", followup)
        self._payroll = _flag("FEATURE_PAYROLL_PACKAGE", payroll)
        self._labels = load_labels()
        self._required = load_required()

    @property
    def cases(self) -> CaseServiceClient:
        return self._cases

    def chat(
        self, message: str, *, case_id: str | None = None, asked_by: str = "recruiter"
    ) -> "ChatReply":
        """One chat message from the recruiter or the Onboarding Team."""
        from .chat import respond

        return respond(self, message, case_id, asked_by=asked_by)

    @property
    def knows(self) -> bool:
        return self._knowledge is not None

    def ask_knowledge(
        self, question: str, *, asked_by: str, channel: str
    ) -> knowledge_agent.KnowledgeAnswer:
        """Route a process question to the Onboarding Knowledge agent (US-025)."""
        if self._knowledge is None:
            raise ValueError("the knowledge base is not available")
        return knowledge_agent.answer(
            question, self._knowledge, asked_by=asked_by, channel=channel
        )

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
        try:
            start_date = date.fromisoformat(start)
        except ValueError:  # an unreadable date is asked for, never guessed
            return StartResult(state="needs_sender", missing=["start_date"])
        data = {
            **reading.values,
            "source": source,
            "source_channel": channel,
            "contradictions": reading.contradictions,
        }
        try:
            case_id = self._cases.create_case(
                CaseIntake(person_ref=person, start_date=start_date, data=data),
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
        # The package cites the recruiter for this value, not the start's channel.
        answered = {**data.get("answered_by", {}), field_name: "recruiter"}
        self._cases.record_answers(
            case_id,
            {
                field_name: value,
                "contradictions": contradictions,
                "answered_by": answered,
            },
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
            sent = self._send_it_request(case_id, package_version, approval_id)
            if sent:
                results.append(sent)
            if self._followup:
                self._send_checklist(case_id, package_version)
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

    def approve_it_request(
        self, case_id: str, *, package_version: int, approver_role: str
    ) -> dict:
        """IT approves the laptop request (US-020); it is sent once both approved."""
        self._cases.record_it_approval(
            case_id, package_version=package_version, approver_role=approver_role
        )
        approval_id = self._cases.approval_id_for(case_id, package_version)
        sent = (
            self._send_it_request(case_id, package_version, approval_id)
            if approval_id
            else None
        )
        return {"case_id": case_id, "it_approved": True, "sent": sent is not None}

    def _send_it_request(
        self, case_id: str, package_version: int, approval_id: str
    ) -> dict | None:
        if not self._cases.has_it_request(case_id, package_version):
            return None
        if not self._cases.it_approved(case_id, package_version):
            notifications.notify(
                self._alerts,
                case_id,
                IT,
                notifications.it_request_text(case_id, package_version),
            )
            self._cases.log_action(case_id, agent=access.AGENT, action="alert_it")
            return None
        return workflow_agent.send_it_request(
            self._workflow,
            approval_id=approval_id,
            package_version=package_version,
            payload=access.it_request(self._cases.case_data(case_id), self._catalog),
        )

    # --- After approval: candidate follow-up, documents, payroll (US-022..024) ---

    def _send_checklist(self, case_id: str, package_version: int) -> None:
        items = followup_agent.checklist(
            self._cases.package_lines(case_id, package_version),
            self._cases.case_data(case_id),
            self._catalog,
        )
        self._cases.send_checklist(case_id, items, agent=followup_agent.AGENT)
        notifications.notify(
            self._alerts,
            case_id,
            CANDIDATE,
            notifications.checklist_text(case_id, [item for item, _ in items]),
        )

    def run_followup(self, case_id: str, *, at_hours: int) -> list[dict]:
        """The reminder run at a (simulated) hour since the checklist was sent. The
        cadence rule is read again on every run (FR-CHK-003)."""
        if at_hours < 0:
            raise ValueError("at_hours must be zero or more")
        if self._cases.case_state(case_id) is not CaseState.DOCUMENTS_PENDING:
            return []
        rule = followup_agent.cadence(RulesCatalog.load())
        outstanding = [
            c["item"]
            for c in self._cases.checklist(case_id)
            if c["status"] == "outstanding"
        ]
        sent = self._cases.reminders(case_id)
        due = followup_agent.due(len(outstanding), sent, rule, at_hours)
        reminders = sum(1 for s in sent if s["kind"] == "reminder")
        for kind, hour in due:
            self._cases.record_reminder(
                case_id,
                kind=kind,
                at_hours=hour,
                rule_id=rule.rule_id,
                agent=followup_agent.AGENT,
            )
            if kind == "reminder":
                reminders += 1
                text = notifications.reminder_text(case_id, outstanding, reminders)
                notifications.notify(self._alerts, case_id, CANDIDATE, text)
            else:
                text = notifications.followup_escalation_text(
                    case_id, outstanding, hour
                )
                notifications.notify(self._alerts, case_id, ONBOARDING, text)
        return [{"kind": kind, "at_hours": hour} for kind, hour in due]

    def record_delivery(
        self, case_id: str, items: list[str], *, recorded_by: str
    ) -> dict:
        """US-023 AC-001: compare the delivery with the checklist; list what is
        missing."""
        missing = self._cases.record_delivery(case_id, items, recorded_by=recorded_by)
        return {"state": self._cases.case_state(case_id).value, "missing": missing}

    def countersign(self, case_id: str, item: str, *, signed_by: str) -> dict:
        self._cases.countersign(case_id, item, signed_by=signed_by)
        return {"item": item, "status": "verified"}

    def approve_payroll_handoff(
        self, case_id: str, *, package_version: int, approved_by: str
    ) -> dict:
        """US-024: the Onboarding Team approves the handoff; the single writer sends
        the package of validated data to Payroll (simulated)."""
        if not self._payroll:
            raise GovernanceError("payroll_package_disabled")
        self._cases.approve_payroll_handoff(
            case_id, package_version=package_version, approved_by=approved_by
        )
        approval_id = self._cases.approval_id_for(case_id, package_version)
        if approval_id is None:
            raise GovernanceError("no_approval")
        payload = workflow_agent.payroll_package(
            self._cases.package_lines(case_id, package_version),
            self._cases.checklist(case_id),
        )
        result = workflow_agent.send_payroll_package(
            self._workflow,
            approval_id=approval_id,
            package_version=package_version,
            payload=payload,
        )
        self._cases.move_case(case_id, CaseState.SENT_TO_PAYROLL, agent=AGENT)
        return {"state": self._cases.case_state(case_id).value, "sent": result}

    def record_payroll_return(self, case_id: str, issue: str) -> dict:
        """US-024 AC-003: an issue Payroll returns becomes a task on the case."""
        task_id = self._cases.record_payroll_return(case_id, issue, agent="payroll")
        notifications.notify(
            self._alerts,
            case_id,
            ONBOARDING,
            notifications.payroll_return_text(case_id),
        )
        return {"task_id": task_id}

    def _equipment_lines(self, data: dict) -> list:
        """S1 lines; a failing Should agent adds an exception and never stops J1."""
        try:
            return access.recommend(data, self._catalog)
        except Exception:  # noqa: BLE001 - any failure becomes a visible exception
            return [
                PackageLine(
                    field="equipment_request",
                    value="Access and Equipment agent failed; IT to prepare it",
                    label="exception",
                    source_or_rule_id=access.AGENT,
                )
            ]

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

    def _start_notes(self, data: dict) -> dict:
        start_id = data.get("jobdiva_start_id")
        if not self._jobdiva or not start_id:
            return {}
        try:
            return self._jobdiva.read_start_notes(str(start_id))
        except KeyError:
            return {}

    def _escalate(self, case_id: str, fields: list[str]) -> None:
        """US-009: Onboarding and HR decide; alerts name fields only (BR-011)."""
        text = notifications.escalation_text(case_id, fields, self._labels)
        for recipient in ("Onboarding Team", "HR"):
            notifications.notify(self._alerts, case_id, recipient, text)
        self._cases.log_action(
            case_id,
            agent=policy.AGENT,
            action="escalate_conflict",
            data_refs={f: policy.CONFLICT_SOURCE for f in fields},
        )

    def _notify_supervisor(self, case_id: str, lines: list) -> None:
        """US-032 AC-001: the supervisor hears of each new hire, then assigns."""
        owner = next(
            (
                line
                for line in lines
                if line.field == "owner" and line.label == "recommended"
            ),
            None,
        )
        if owner is None:
            return
        notifications.notify(
            self._alerts,
            case_id,
            SUPERVISOR,
            notifications.owner_text(case_id, owner.value, owner.source_or_rule_id),
        )
        self._cases.log_action(
            case_id,
            agent=AGENT,
            action="notify_supervisor",
            rule_ids=[owner.source_or_rule_id],
            data_refs={"owner": owner.source_or_rule_id},
        )

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
        self._set_up(case_id, data)
        return StartResult(state=self._cases.case_state(case_id).value, case_id=case_id)

    def _set_up(self, case_id: str, data: dict) -> int:
        """Build the package for a case in Case set up; returns its version."""
        conflicts = policy.find_conflicts(data, self._start_notes(data))
        lines = policy.recommend(data, self._catalog, conflicts)
        if self._access:
            lines += self._equipment_lines(data)
        version = self._cases.build_package(
            case_id, lines, agent=policy.AGENT, escalated=bool(conflicts)
        )
        if conflicts:
            self._escalate(case_id, list(conflicts))
        if version == 1:  # the supervisor hears of each new hire once
            self._notify_supervisor(case_id, lines)
        return version

    def review_recommendation(
        self,
        case_id: str,
        field_name: str,
        *,
        reviewed_by: str,
        confirm: bool = False,
        values: list[str] | None = None,
    ) -> dict:
        """US-026 (BR-006): the Onboarding Team confirms the recommended path or
        paperwork, or changes it. A change rebuilds the package as a new version,
        so approvals of the earlier version no longer apply."""
        if field_name not in policy.REVIEWABLE:
            raise ValueError("only path or paperwork can be reviewed")
        values = [v.strip() for v in values or [] if v.strip()]
        if not confirm and not values:
            raise ValueError("a change needs at least one value")
        action = "confirm_recommendation" if confirm else "change_recommendation"
        self._require_review(case_id, agent=reviewed_by, action=action)
        version = self._cases.current_package_version(case_id)
        if not confirm:
            # Leave Ready for review first: if the approver decided meanwhile the
            # move is refused and the team's change is never stored.
            self._move_or_refuse(case_id, agent=reviewed_by, action=action)
        data = self._cases.case_data(case_id)
        entry = {"confirmed": True} if confirm else {"values": values}
        review = {
            **data.get("team_review", {}),
            field_name: entry | {"version": version},
        }
        self._cases.record_answers(
            case_id, {"team_review": review}, agent=reviewed_by, source=policy.TEAM
        )
        self._cases.log_action(
            case_id,
            agent=reviewed_by,
            action=action,
            data_refs={field_name: policy.TEAM},
        )
        if not confirm:
            version = self._set_up(case_id, self._cases.case_data(case_id))
        return {
            "state": self._cases.case_state(case_id).value,
            "package_version": version,
        }

    def _require_review(self, case_id: str, *, agent: str, action: str) -> None:
        """Team and HR inputs apply only while the package awaits review."""
        if self._cases.case_state(case_id) is not CaseState.READY_FOR_REVIEW:
            self._refuse(
                case_id, agent=agent, action=action, reason="case_not_in_review"
            )

    def _move_or_refuse(self, case_id: str, *, agent: str, action: str) -> None:
        try:
            self._cases.move_case(case_id, CaseState.CASE_SET_UP, agent=policy.AGENT)
        except InvalidTransition:
            self._refuse(
                case_id, agent=agent, action=action, reason="case_not_in_review"
            )

    def _refuse(self, case_id: str, *, agent: str, action: str, reason: str) -> None:
        """Audit a refusal before it reaches the caller (US-018)."""
        self._cases.log_action(
            case_id,
            agent=agent,
            action=action,
            outcome="refused",
            data_refs={"reason": reason},
        )
        raise GovernanceError(reason)

    def record_hr_answer(
        self, case_id: str, field_name: str, value: str, *, recorded_by: str
    ) -> dict:
        """US-027: the Onboarding Team records HR's answer to an escalated FLSA or
        classification conflict; the package is rebuilt as a new version (BR-001).
        Without an answer the case stays escalated and no value is chosen."""
        action = "record_hr_answer"
        self._require_review(case_id, agent=recorded_by, action=action)
        data = self._cases.case_data(case_id)
        if field_name not in policy.find_conflicts(data, self._start_notes(data)):
            raise ValueError(f"no open conflict for {field_name!r} on this case")
        self._move_or_refuse(case_id, agent=recorded_by, action=action)
        answered = {**data.get("answered_by", {}), field_name: policy.HR}
        self._cases.record_answers(
            case_id,
            {field_name: value, "answered_by": answered},
            agent=recorded_by,
            source=policy.HR,
        )
        version = self._set_up(case_id, self._cases.case_data(case_id))
        return {
            "state": self._cases.case_state(case_id).value,
            "package_version": version,
        }
