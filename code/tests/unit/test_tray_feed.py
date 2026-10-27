"""Coworker Tray: only alerts not shown yet are notified, and each opens its case."""

from desktop.feed import AlertFeed, case_url, window_url


def _alerts(*ids: int) -> list[dict]:
    return [{"id": i, "case_id": f"case-{i}", "text": f"alert {i}"} for i in ids]


def test_first_poll_shows_nothing_old() -> None:
    feed = AlertFeed()

    assert feed.new(_alerts(3, 2, 1)) == []
    assert feed.last_id == 3
    assert [a["id"] for a in feed.recent] == [3, 2, 1]


def test_only_new_alerts_are_returned_oldest_first() -> None:
    feed = AlertFeed()
    feed.new(_alerts(1, 2))

    fresh = feed.new(_alerts(4, 3, 2, 1))

    assert [a["id"] for a in fresh] == [3, 4]
    assert feed.unseen == 2
    assert feed.new(_alerts(4, 3, 2, 1)) == []


def test_recent_keeps_the_five_latest() -> None:
    feed = AlertFeed()

    feed.new(_alerts(*range(1, 9)))

    assert [a["id"] for a in feed.recent] == [8, 7, 6, 5, 4]


def test_a_new_role_starts_fresh() -> None:
    feed = AlertFeed()
    feed.new(_alerts(1))
    feed.new(_alerts(1, 2))

    feed.reset()

    assert (feed.last_id, feed.unseen, feed.recent) == (None, 0, [])
    assert feed.new(_alerts(1, 2)) == []


def test_link_opens_the_case_as_the_tray_role() -> None:
    assert (
        case_url("http://127.0.0.1:3000/", "case-abc", "ldc")
        == "http://127.0.0.1:3000/?role=ldc#status/case-abc"
    )
    assert case_url("http://127.0.0.1:3000", None, "it").endswith("?role=it#dashboard")


def test_icon_shows_a_red_dot_for_new_alerts() -> None:
    from desktop.tray import ALERT, icon_image

    quiet = icon_image(0, connected=True)
    busy = icon_image(2, connected=True)

    assert quiet.getpixel((52, 12))[:3] != ALERT
    assert busy.getpixel((52, 12))[:3] == ALERT


def test_the_window_docks_above_the_clock() -> None:
    from desktop.window import HEIGHT, WIDTH, docked

    x, y = docked(1920, 1080)

    assert (x + WIDTH, y + HEIGHT) == (1920 - 12, 1080 - 48 - 12)
    assert docked(400, 300) == (0, 0)  # a small screen keeps it on screen


def test_the_window_opens_the_chat_on_the_case() -> None:
    assert (
        window_url("http://127.0.0.1:3000", "case-abc", "approver")
        == "http://127.0.0.1:3000/?role=approver&mode=desktop#chat/case-abc"
    )
    assert window_url("http://127.0.0.1:3000", None, "it").endswith("#chat")


def test_notification_names_the_case_and_counts_the_rest() -> None:
    from desktop.notifier import headline

    title, body = headline({"case_id": "case-abc", "text": "Missing: Bill rate."}, 2)

    assert title == "New onboarding alert"
    assert body == "Missing: Bill rate.  (+2 more)"


def test_without_toasts_the_plain_notification_is_used(tmp_path, monkeypatch) -> None:
    from desktop import notifier as module

    monkeypatch.setattr(module.sys, "platform", "linux")
    shown = []
    notifier = module.Notifier(
        tmp_path / "logo.png",
        lambda case: None,
        lambda body, title: shown.append((title, body)),
    )

    notifier.show({"case_id": "case-1", "text": "Hi"}, 0, "Recruiter")

    assert shown == [("New onboarding alert", "Hi")]


def test_the_logo_is_drawn_large_and_sharp() -> None:
    from desktop.tray import icon_image

    assert icon_image(0, True, size=256).size == (256, 256)


def test_about_describes_the_coworker_by_inspyr_velocity() -> None:
    from desktop.feed import ABOUT

    assert "By INSPYR Velocity" in ABOUT
    assert "approves the package" in ABOUT
