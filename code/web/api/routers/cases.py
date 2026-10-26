from typing import Literal

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
