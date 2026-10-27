from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..deps import Coworker, Mailbox, Role

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


class NewEmail(BaseModel):
    sender: str = Field(
        min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8000)


@router.get("")
def list_messages(mailbox: Mailbox, role: Role) -> list[dict]:
    return mailbox.list_messages()


@router.post("")
def receive_email(
    email: NewEmail, mailbox: Mailbox, coworker: Coworker, role: Role
) -> dict:
    """A start email arrives in the onboarding mailbox; the Coworker processes it at
    once (US-001). Synthetic data only: nothing reaches a real mailbox."""
    message_id = mailbox.deliver(email.sender, email.subject, email.body)
    try:
        outcome = asdict(coworker.process_start(email.body, source=email.sender))
    except ValueError as exc:
        mailbox.record_outcome(message_id, None, "failed")
        raise HTTPException(400, detail=str(exc)) from None
    mailbox.record_outcome(message_id, outcome["case_id"], outcome["state"])
    return {"message_id": message_id, **outcome}


@router.post("/{message_id}/process")
def process_message(
    message_id: str, mailbox: Mailbox, coworker: Coworker, role: Role
) -> dict:
    """Simulates the start email arriving: the Coworker processes it (US-037 AC-002)."""
    try:
        message = mailbox.read_message(message_id)
    except KeyError:
        raise HTTPException(404, detail=f"No message {message_id!r}") from None
    return asdict(coworker.process_start(message["body"], source=message["from"]))
