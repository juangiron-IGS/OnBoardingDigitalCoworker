from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.common.model_client import get_model_client
from agents.onboarding_knowledge import agent as knowledge_agent

from ..deps import Knowledge, Role

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class Validation(BaseModel):
    decision: Literal["validated", "rejected"]


@router.get("")
def overview(kb: Knowledge, role: Role) -> dict:
    """The knowledge view: records with their status and pending questions."""
    return {"records": kb.records(), "pending": kb.pending()}


@router.post("/ask")
def ask(body: Question, kb: Knowledge, role: Role) -> dict:
    """Ask the Onboarding Knowledge agent (US-025)."""
    try:
        result = knowledge_agent.answer(
            body.question, kb, asked_by=role, channel="web", model=get_model_client()
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from None
    return asdict(result)


@router.post("/{record_id}/validation")
def validate(record_id: str, body: Validation, kb: Knowledge, role: Role) -> dict:
    """The Onboarding Team validates or rejects a record (FR-KB-003)."""
    if role != "onboarding":
        raise HTTPException(403, detail="Only the Onboarding Team validates knowledge")
    try:
        kb.validate(record_id, body.decision, decided_by=role)
    except KeyError:
        raise HTTPException(404, detail=f"No knowledge record {record_id}") from None
    return {"record_id": record_id, "status": body.decision}
