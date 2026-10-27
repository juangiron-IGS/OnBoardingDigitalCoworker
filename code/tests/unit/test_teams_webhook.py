"""The optional Teams channel mirror: off by default, and a failure never breaks
the alert (the Teams mock still records it)."""

import httpx

from mcp_servers.mocks.teams import webhook


def test_the_mirror_is_off_without_a_webhook_url(monkeypatch) -> None:
    monkeypatch.delenv("TEAMS_WEBHOOK_URL", raising=False)

    assert webhook.mirror("Recruiter", "SYN-0043 needs your answer.") is False


def test_the_alert_goes_as_an_adaptive_card(monkeypatch) -> None:
    sent = {}
    monkeypatch.setattr(
        webhook.httpx,
        "post",
        lambda url, json, timeout: (
            sent.update(url=url, json=json) or httpx.Response(202)
        ),
    )

    webhook._post("https://example.invalid/hook", webhook.card("IT", "Approve v1."))

    card = sent["json"]["attachments"][0]["content"]
    assert card["type"] == "AdaptiveCard"
    assert card["body"][1]["text"] == "Approve v1."


def test_a_failing_webhook_is_logged_without_its_url(monkeypatch, caplog) -> None:
    def fail(url, json, timeout):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(webhook.httpx, "post", fail)

    webhook._post("https://secret.example/hook?sig=abc", webhook.card("IT", "x"))

    assert "unreachable" in caplog.text
    assert "sig=abc" not in caplog.text
