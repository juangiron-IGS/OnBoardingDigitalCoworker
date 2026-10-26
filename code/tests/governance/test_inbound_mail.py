"""A new start email arrives in the simulated onboarding mailbox (US-001, US-037)."""

from pathlib import Path

import pytest

from mcp_servers.mocks.outlook.service import MailboxService

pytestmark = pytest.mark.db

MAILBOX = Path(__file__).resolve().parents[2] / "db" / "seed" / "mailbox"


def test_delivered_email_is_listed_first_and_readable(app_conn) -> None:
    mailbox = MailboxService(MAILBOX, app_conn)

    message_id = mailbox.deliver(
        "recruiter.sam@example.com", "New start - SYN-0070", "Candidate ID: SYN-0070"
    )

    first = mailbox.list_messages()[0]
    assert first["id"] == message_id
    assert first["subject"] == "New start - SYN-0070"
    assert mailbox.read_message(message_id)["body"] == "Candidate ID: SYN-0070"


def test_outcome_is_kept_with_the_email(app_conn) -> None:
    mailbox = MailboxService(MAILBOX, app_conn)
    message_id = mailbox.deliver("a@example.com", "Start", "Candidate ID: SYN-0071")

    mailbox.record_outcome(message_id, "case-abc", "needs_clarification")

    first = mailbox.list_messages()[0]
    assert (first["case_id"], first["outcome"]) == ("case-abc", "needs_clarification")


def test_unknown_delivered_id_is_refused(app_conn) -> None:
    with pytest.raises(KeyError):
        MailboxService(MAILBOX, app_conn).read_message("mail-999999")
