"""Coworker Tray: the Onboarding Coworker in the Windows notification area.

A small icon next to the clock shows a Windows notification when an alert arrives
for the chosen role, and opens the web app on that case. It reads alerts over MCP
only; approvals and actions stay with people in the web app (BR-002).

Run from code/: .venv/Scripts/python -m desktop.tray   (or ./scripts/tray.sh)
"""

import asyncio
import os
import threading
import webbrowser

import pystray
from PIL import Image, ImageDraw

from .feed import ROLES, AlertFeed, case_url, title
from .poller import poll, server_params

ACCENT = (31, 95, 174)
ALERT = (214, 48, 49)


def icon_image(unseen: int, connected: bool) -> Image.Image:
    """A blue tile with a tick; grey when disconnected; a red dot for new alerts."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (4, 4, 60, 60), radius=14, fill=ACCENT if connected else (128, 128, 128)
    )
    draw.line((18, 34, 28, 44, 46, 22), fill="white", width=7, joint="curve")
    if unseen:
        draw.ellipse((40, 0, 64, 24), fill=ALERT, outline="white", width=2)
    return image


class CoworkerTray:
    def __init__(self, role: str, app_url: str) -> None:
        self.role = role
        self.app_url = app_url
        self.feed = AlertFeed()
        self.paused = False
        self.connected = False
        self._stop: asyncio.Event | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.icon = pystray.Icon(
            "onboarding-coworker",
            icon_image(0, False),
            self._tooltip(),
            menu=self._menu(),
        )

    # --- MCP polling, on its own thread with its own event loop ---

    def _start_polling(self) -> None:
        def run() -> None:
            self._loop = asyncio.new_event_loop()
            self._stop = asyncio.Event()
            self._loop.run_until_complete(
                poll(
                    server_params(self.role),
                    self._on_alerts,
                    self._on_status,
                    self._stop,
                )
            )

        threading.Thread(target=run, daemon=True).start()

    def _stop_polling(self) -> None:
        if self._loop and self._stop:
            self._loop.call_soon_threadsafe(self._stop.set)

    def _on_status(self, status: str) -> None:
        self.connected = status == "connected"
        self._refresh()

    def _on_alerts(self, alerts: list[dict]) -> None:
        fresh = self.feed.new(alerts)
        if fresh and not self.paused:
            latest = fresh[-1]
            more = f" (+{len(fresh) - 1} more)" if len(fresh) > 1 else ""
            self.icon.notify(latest["text"] + more, title(latest))
        self._refresh()

    # --- icon and menu ---

    def _tooltip(self) -> str:
        state = (
            "paused"
            if self.paused
            else ("connected" if self.connected else "connecting")
        )
        return f"Onboarding Coworker · {ROLES[self.role]} · {state}"

    def _refresh(self) -> None:
        self.icon.icon = icon_image(self.feed.unseen, self.connected)
        self.icon.title = self._tooltip()
        self.icon.update_menu()

    def _menu(self) -> pystray.Menu:
        def recent_items():  # noqa: ANN202 - rebuilt each time the menu opens
            if not self.feed.recent:
                yield pystray.MenuItem("No alerts yet", None, enabled=False)
            for alert in self.feed.recent:
                text = (
                    alert["text"]
                    if len(alert["text"]) <= 70
                    else alert["text"][:67] + "..."
                )
                yield pystray.MenuItem(text, self._opener(alert.get("case_id")))

        roles = pystray.Menu(
            *(
                pystray.MenuItem(
                    label,
                    self._role_setter(key),
                    checked=lambda item, key=key: self.role == key,
                    radio=True,
                )
                for key, label in ROLES.items()
            )
        )
        return pystray.Menu(
            pystray.MenuItem("Open latest alert", self._open_latest, default=True),
            pystray.MenuItem("Open the Coworker", self._opener(None)),
            pystray.MenuItem("Latest alerts", pystray.Menu(recent_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Role", roles),
            pystray.MenuItem(
                "Pause notifications",
                self._toggle_pause,
                checked=lambda item: self.paused,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _opener(self, case_id: str | None):  # noqa: ANN202
        def open_case(icon, item) -> None:  # noqa: ANN001
            self.feed.mark_seen()
            webbrowser.open(case_url(self.app_url, case_id, self.role))
            self._refresh()

        return open_case

    def _open_latest(self, icon, item) -> None:  # noqa: ANN001
        latest = self.feed.recent[0] if self.feed.recent else None
        self._opener(latest.get("case_id") if latest else None)(icon, item)

    def _role_setter(self, role: str):  # noqa: ANN202
        def set_role(icon, item) -> None:  # noqa: ANN001
            if role == self.role:
                return
            self._stop_polling()
            self.role = role
            self.feed.reset()
            self.connected = False
            self._refresh()
            self._start_polling()

        return set_role

    def _toggle_pause(self, icon, item) -> None:  # noqa: ANN001
        self.paused = not self.paused
        self._refresh()

    def _quit(self, icon, item) -> None:  # noqa: ANN001
        self._stop_polling()
        icon.stop()

    def run(self) -> None:
        self._start_polling()
        self.icon.run()


def main() -> None:
    role = os.environ.get("COWORKER_TRAY_ROLE") or "recruiter"
    if role not in ROLES:
        raise SystemExit(f"COWORKER_TRAY_ROLE must be one of {sorted(ROLES)}")
    port = os.environ.get("WEB_APP_PORT") or "3000"
    CoworkerTray(role, f"http://127.0.0.1:{port}").run()


if __name__ == "__main__":
    main()
