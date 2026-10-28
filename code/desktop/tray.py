"""Coworker Tray: the Onboarding Coworker in the Windows notification area.

A small icon next to the clock shows a Windows notification when an alert arrives
for the chosen role. A click on the icon opens the Coworker window docked above the
clock: the web app itself (chat, approval and every other view) on that case. The
tray reads alerts over MCP only; approvals and actions stay with people in the web
app (BR-002).

Run from code/: .venv/Scripts/python -m desktop.tray   (or ./scripts/tray.sh)
"""

import asyncio
import ctypes
import os
import threading
import webbrowser

import pystray
from PIL import Image, ImageDraw

from .feed import (
    ABOUT,
    ALL,
    RECIPIENT_ROLE,
    ROLES,
    THEMES,
    AlertFeed,
    action,
    case_url,
    window_url,
)
from .notifier import Notifier, logo_path, use_app_identity
from .poller import poll, server_params
from .window import CoworkerWindow

ACCENT = (0, 128, 128)  # teal, as the notification header (BRAND)
ALERT = (214, 48, 49)


def icon_image(unseen: int, connected: bool, size: int = 64) -> Image.Image:
    """A new hire with a plus on a teal disc; grey when disconnected; a red dot for
    new alerts. Drawn on a 64-unit grid and scaled, so the logo stays sharp."""
    k = size / 64
    fill = ACCENT if connected else (128, 128, 128)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((2 * k, 2 * k, 62 * k, 62 * k), fill=fill)
    draw.ellipse((22 * k, 13 * k, 38 * k, 29 * k), fill="white")  # head
    draw.pieslice((13 * k, 31 * k, 47 * k, 65 * k), 180, 360, fill="white")  # body
    draw.ellipse((40 * k, 34 * k, 60 * k, 54 * k), fill="white")  # plus badge
    bar = round(4 * k)
    draw.line((50 * k, 38 * k, 50 * k, 50 * k), fill=fill, width=bar)
    draw.line((44 * k, 44 * k, 56 * k, 44 * k), fill=fill, width=bar)
    if unseen:
        draw.ellipse(
            (40 * k, 0, 64 * k, 24 * k),
            fill=ALERT,
            outline="white",
            width=max(2, round(2 * k)),
        )
    return image


class CoworkerTray:
    def __init__(self, role: str, app_url: str, *, window: bool = True) -> None:
        self.role = role
        self.theme = "system"
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
        self.window = (
            CoworkerWindow(window_url(app_url, None, self._view_role()))
            if window
            else None
        )
        logo = logo_path()
        icon_image(0, True, size=256).save(logo)
        # The window's own icon on the taskbar and in its title bar.
        self.window_icon = logo.with_suffix(".ico")
        icon_image(0, True, size=256).save(
            self.window_icon, sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
        )
        self.notifier = Notifier(logo, self._open_case, self.icon.notify)

    # --- MCP polling, on its own thread with its own event loop ---

    def _start_polling(self) -> None:
        def run() -> None:
            self._loop = asyncio.new_event_loop()
            self._stop = asyncio.Event()
            self._loop.run_until_complete(
                poll(
                    # "All teams" reads every team's alerts through any valid role
                    server_params("onboarding" if self.role == ALL else self.role),
                    self._on_alerts,
                    self._on_status,
                    self._stop,
                    all_teams=self.role == ALL,
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
            # One notification per alert (the latest three), so each team sees its own
            shown = fresh[-3:]
            for i, alert in enumerate(shown):
                more = len(fresh) - len(shown) if i == len(shown) - 1 else 0
                self.notifier.show(alert, more, ROLES[self.role])
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
                yield pystray.MenuItem(text, self._opener(alert.get("case_id"), alert))

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
        themes = pystray.Menu(
            *(
                pystray.MenuItem(
                    label,
                    self._theme_setter(key),
                    checked=lambda item, key=key: self.theme == key,
                    radio=True,
                )
                for key, label in THEMES.items()
            )
        )
        return pystray.Menu(
            pystray.MenuItem("Open latest alert", self._open_latest, default=True),
            pystray.MenuItem("Open the Coworker", self._opener(None)),
            pystray.MenuItem("Open in the browser", self._browser),
            pystray.MenuItem("Latest alerts", pystray.Menu(recent_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Role", roles),
            pystray.MenuItem("Theme", themes),
            pystray.MenuItem(
                "Fixed window width (20%)",
                self._toggle_fixed,
                checked=lambda item: self.window is None or self.window.fixed,
            ),
            pystray.MenuItem(
                "Pause notifications",
                self._toggle_pause,
                checked=lambda item: self.paused,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("About the Coworker", self._about),
            pystray.MenuItem("Quit", self._quit),
        )

    def _view_role(self, recipient: str | None = None) -> str:
        """The role the window opens as: the alert's team with "All teams"."""
        if self.role != ALL:
            return self.role
        return RECIPIENT_ROLE.get(recipient or "", "onboarding")

    def _open_case(
        self, case_id: str | None, view: str = "chat", recipient: str | None = None
    ) -> None:
        """From the menu, the icon or a click on a notification (on its view)."""
        self.feed.mark_seen()
        role = self._view_role(recipient)
        if self.window:
            self.window.open(window_url(self.app_url, case_id, role, self.theme, view))
        else:
            webbrowser.open(case_url(self.app_url, case_id, role))
        self._refresh()

    def _opener(self, case_id: str | None, alert: dict | None = None):  # noqa: ANN202
        """Open the case; for an alert, as its team and on the view its step needs."""
        if alert is None:
            return lambda icon, item: self._open_case(case_id)
        view = action(alert)[3]
        return lambda icon, item: self._open_case(case_id, view, alert.get("recipient"))

    def _browser(self, icon, item) -> None:  # noqa: ANN001
        webbrowser.open(case_url(self.app_url, None, self._view_role()))

    def _open_latest(self, icon, item) -> None:  # noqa: ANN001
        latest = self.feed.recent[0] if self.feed.recent else None
        self._opener(latest.get("case_id") if latest else None, latest)(icon, item)

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

    def _about(self, icon, item) -> None:  # noqa: ANN001
        # A native message box, on its own thread so the tray keeps running.
        threading.Thread(
            target=ctypes.windll.user32.MessageBoxW,
            args=(0, ABOUT, "About the Onboarding Coworker", 0x40 | 0x40000),
            daemon=True,
        ).start()

    def _toggle_fixed(self, icon, item) -> None:  # noqa: ANN001
        if self.window:
            self.window.set_fixed(not self.window.fixed)

    def _theme_setter(self, theme: str):  # noqa: ANN202
        def set_theme(icon, item) -> None:  # noqa: ANN001
            self.theme = theme
            if self.window:
                self.window.set_theme(theme)

        return set_theme

    def _toggle_pause(self, icon, item) -> None:  # noqa: ANN001
        self.paused = not self.paused
        self._refresh()

    def _quit(self, icon, item) -> None:  # noqa: ANN001
        self._stop_polling()
        icon.stop()
        if self.window:
            self.window.destroy()

    def run(self) -> None:
        self._start_polling()
        if not self.window:
            self.icon.run()
            return
        # The window loop needs the main thread; the icon runs beside it.
        self.icon.run_detached()
        CoworkerWindow.start(self.window_icon)
        self.icon.stop()


def main() -> None:
    role = os.environ.get("COWORKER_TRAY_ROLE") or "recruiter"
    if role not in ROLES:
        raise SystemExit(f"COWORKER_TRAY_ROLE must be one of {sorted(ROLES)}")
    port = os.environ.get("WEB_APP_PORT") or "3000"
    use_app_identity()  # before any window exists
    CoworkerTray(role, f"http://127.0.0.1:{port}").run()


if __name__ == "__main__":
    main()
