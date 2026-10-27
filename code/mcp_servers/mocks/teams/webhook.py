"""Optional mirror of the Teams mock's alerts to one real Teams channel, through a
Teams Workflows webhook ("Post to a channel when a webhook request is received").

Off unless TEAMS_WEBHOOK_URL is set in code/.env. One way only: nobody answers the
Coworker from Teams, approvals stay in the web app (BR-002). Alerts already carry
field names, never restricted values (BR-011). The mirror runs on its own thread,
so a slow or failing webhook never delays or breaks the alert; the URL is a
secret and is never logged.
"""

import logging
import os
import threading

import httpx

logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 5


def mirror(recipient: str, text: str) -> bool:
    """Send the alert to the channel in the background; False when it is off."""
    url = os.environ.get("TEAMS_WEBHOOK_URL", "").strip()
    if not url.startswith("https://"):
        return False
    threading.Thread(
        target=_post, args=(url, card(recipient, text)), daemon=True
    ).start()
    return True


def card(recipient: str, text: str) -> dict:
    """The alert as an Adaptive Card, the format Teams Workflows expects."""
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"Onboarding Coworker · alert to {recipient}",
                            "weight": "Bolder",
                            "wrap": True,
                        },
                        {"type": "TextBlock", "text": text, "wrap": True},
                        {
                            "type": "TextBlock",
                            "text": "Synthetic data · act in the Coworker app",
                            "isSubtle": True,
                            "size": "Small",
                            "wrap": True,
                        },
                    ],
                },
            }
        ],
    }


def _post(url: str, payload: dict) -> None:
    try:
        response = httpx.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        if response.status_code >= 300:
            logger.warning("teams webhook refused the alert: %s", response.status_code)
    except httpx.HTTPError as error:
        logger.warning("teams webhook unreachable: %s", type(error).__name__)
