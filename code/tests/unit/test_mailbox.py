from pathlib import Path

import pytest

from contracts.mcp_tools import Mailbox
from mcp_servers.mocks.outlook.service import MailboxService

MAILBOX = Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"


def test_mailbox_lists_the_seed_emails() -> None:
    messages = MailboxService(MAILBOX).list_messages()

    assert [m["id"] for m in messages][:2] == [
        "01_complete_and_consistent",
        "02_missing_two_fields",
    ]
    assert all(m["subject"] and m["from"] for m in messages)


def test_read_message_returns_headers_and_body() -> None:
    message = MailboxService(MAILBOX).read_message("02_missing_two_fields")

    assert message["from"] == "recruiter.sam@example.com"
    assert "Candidate ID: SYN-0043" in message["body"]


@pytest.mark.parametrize(
    "bad", ["../../.env", "nope", "01_complete_and_consistent.eml"]
)
def test_read_message_refuses_unknown_ids(bad: str) -> None:
    with pytest.raises(KeyError):
        MailboxService(MAILBOX).read_message(bad)


def test_mailbox_fulfils_the_contract() -> None:
    assert isinstance(MailboxService(MAILBOX), Mailbox)
