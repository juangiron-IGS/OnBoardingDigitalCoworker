from email import policy
from email.message import EmailMessage
from email.parser import Parser
from pathlib import Path

SEED_MAILBOX = Path(__file__).resolve().parents[3] / "db" / "seed" / "mailbox"


class MailboxService:
    """The onboarding mailbox mock: synthetic start emails stored as .eml files.

    Implements contracts.mcp_tools.Mailbox. A message ID is a file name without
    its extension, and only IDs from list_messages() can be read.
    """

    def __init__(self, folder: Path = SEED_MAILBOX) -> None:
        self._folder = folder

    def list_messages(self) -> list[dict]:
        return [self._headers(path) for path in sorted(self._folder.glob("*.eml"))]

    def read_message(self, message_id: str) -> dict:
        paths = {path.stem: path for path in self._folder.glob("*.eml")}
        if message_id not in paths:
            raise KeyError(message_id)
        message = self._parse(paths[message_id])
        return {**self._headers(paths[message_id]), "body": message.get_content()}

    def _headers(self, path: Path) -> dict:
        message = self._parse(path)
        return {"id": path.stem, "from": message["From"], "subject": message["Subject"]}

    @staticmethod
    def _parse(path: Path) -> EmailMessage:
        return Parser(policy=policy.default).parsestr(path.read_text(encoding="utf-8"))
