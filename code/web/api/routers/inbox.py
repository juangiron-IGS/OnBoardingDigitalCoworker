from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from ..deps import Coworker, Mailbox, Role

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


@router.get("")
def list_messages(mailbox: Mailbox, role: Role) -> list[dict]:
    return mailbox.list_messages()


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
