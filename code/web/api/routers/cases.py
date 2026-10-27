from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.case_service.domain.errors import GovernanceError

from ..deps import Cases, Coworker, Role

router = APIRouter(prefix="/api/cases", tags=["cases"])


class Answer(BaseModel):
    field: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=500)


class Decision(BaseModel):
    package_version: int = Field(ge=1)
    decision: Literal["approve", "return", "reject"]
    comment: str | None = Field(default=None, max_length=1000)


class Owner(BaseModel):
    owner: str = Field(min_length=1, max_length=120)


@router.get("")
def list_cases(cases: Cases, role: Role) -> list[dict]:
    return cases.list_cases()


@router.get("/{case_id}")
def get_case(case_id: str, cases: Cases, coworker: Coworker, role: Role) -> dict:
    view = cases.case_view(case_id, role=role)
    if view is None:
        raise HTTPException(404, detail=f"No case {case_id!r}")
    view["questions"] = coworker.questions(case_id)
    return view


@router.post("/{case_id}/answers")
def answer(case_id: str, body: Answer, coworker: Coworker, role: Role) -> dict:
    try:
        state = coworker.answer(case_id, body.field, body.value)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from None
    except GovernanceError as refusal:
        raise HTTPException(409, detail={"refused": refusal.reason}) from None
    return {"case_id": case_id, "state": state}


@router.post("/{case_id}/owner")
def assign_owner(case_id: str, body: Owner, cases: Cases, role: Role) -> dict:
    """The Consultant Onboarding Supervisor assigns the follow-up owner (US-032)."""
    if role != "approver":
        raise HTTPException(403, detail="Only the approver can assign the owner")
    try:
        cases.assign_owner(case_id, body.owner.strip(), assigned_by=role)
    except GovernanceError as refusal:
        raise HTTPException(409, detail={"refused": refusal.reason}) from None
    return {"case_id": case_id, "assigned_owner": body.owner.strip()}


class ItApproval(BaseModel):
    package_version: int = Field(ge=1)


@router.post("/{case_id}/it-approval")
def approve_it_request(
    case_id: str, body: ItApproval, coworker: Coworker, cases: Cases, role: Role
) -> dict:
    """IT approves the access and laptop request (US-020, BR-012)."""
    if role != "it":
        raise HTTPException(403, detail="Only IT can approve the laptop request")
    try:
        return coworker.approve_it_request(
            case_id, package_version=body.package_version, approver_role=role
        )
    except GovernanceError as refusal:
        raise HTTPException(
            409,
            detail={
                "refused": refusal.reason,
                "current_version": cases.current_package_version(case_id),
            },
        ) from None


class Review(BaseModel):
    field: Literal["path", "paperwork"]
    action: Literal["confirm", "change"]
    values: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(
        default_factory=list, max_length=20
    )


@router.post("/{case_id}/recommendation")
def review_recommendation(
    case_id: str, body: Review, coworker: Coworker, cases: Cases, role: Role
) -> dict:
    """The Onboarding Team confirms or changes the path or paperwork (US-026)."""
    if role != "onboarding":
        raise HTTPException(403, detail="Only the Onboarding Team reviews this")
    try:
        return coworker.review_recommendation(
            case_id,
            body.field,
            reviewed_by=role,
            confirm=body.action == "confirm",
            values=body.values,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from None
    except GovernanceError as refusal:
        raise HTTPException(
            409,
            detail={
                "refused": refusal.reason,
                "current_version": cases.current_package_version(case_id),
            },
        ) from None


class HrAnswer(BaseModel):
    field: Literal["flsa", "employment_type"]
    value: str = Field(min_length=1, max_length=60)


@router.post("/{case_id}/hr-answer")
def record_hr_answer(
    case_id: str, body: HrAnswer, coworker: Coworker, role: Role
) -> dict:
    """The Onboarding Team records HR's answer to an escalated conflict (US-027)."""
    if role != "onboarding":
        raise HTTPException(403, detail="Only the Onboarding Team records HR's answer")
    try:
        return coworker.record_hr_answer(
            case_id, body.field, body.value.strip(), recorded_by=role
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from None
    except GovernanceError as refusal:
        raise HTTPException(409, detail={"refused": refusal.reason}) from None


@router.post("/{case_id}/decision")
def decide(
    case_id: str, body: Decision, coworker: Coworker, cases: Cases, role: Role
) -> dict:
    if role != "approver":
        raise HTTPException(403, detail="Only the approver can decide on a package")
    try:
        return coworker.decide(
            case_id,
            package_version=body.package_version,
            decision=body.decision,
            approver_role=role,
            comment=body.comment,
        )
    except GovernanceError as refusal:
        raise HTTPException(
            409,
            detail={
                "refused": refusal.reason,
                "current_version": cases.current_package_version(case_id),
            },
        ) from None


chat_router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    case_id: str | None = Field(default=None, max_length=64)


@chat_router.post("")
def chat(body: ChatMessage, coworker: Coworker, role: Role) -> dict:
    """The chat view (US-002, US-003, US-019)."""
    try:
        reply = coworker.chat(body.message, case_id=body.case_id, asked_by=role)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from None
    except GovernanceError as refusal:
        raise HTTPException(409, detail={"refused": refusal.reason}) from None
    return {
        "reply": reply.reply,
        "case_id": reply.case_id,
        "state": reply.state,
        "asking": reply.asking,
    }
