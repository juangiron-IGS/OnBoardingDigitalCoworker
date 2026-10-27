"""The Coworker window the tray opens: the web app itself (chat, inbox, approval,
dashboard, status, knowledge) in a compact desktop window docked above the clock,
like a chat popup. Same pages and same controls as the browser, so every approval
still goes through the web app's governance (BR-002)."""

from pathlib import Path

WIDTH, HEIGHT = 500, 800
MARGIN, TASKBAR = 12, 48


def docked(screen_width: int, screen_height: int) -> tuple[int, int]:
    """Top-left corner that docks the window at the bottom right, above the taskbar."""
    x = max(0, screen_width - WIDTH - MARGIN)
    y = max(0, screen_height - HEIGHT - TASKBAR - MARGIN)
    return x, y


class CoworkerWindow:
    """One pywebview window, created hidden and shown on demand. Closing it only
    hides it; it is destroyed when the tray quits."""

    def __init__(self, url: str) -> None:
        import webview  # the GUI toolkit loads only when the window is used

        screen = webview.screens[0] if webview.screens else None
        x, y = docked(screen.width, screen.height) if screen else (None, None)
        self._quitting = False
        self._window = webview.create_window(
            "Onboarding Coworker",
            url,
            width=WIDTH,
            height=HEIGHT,
            x=x,
            y=y,
            min_size=(420, 560),
            hidden=True,
            text_select=True,  # pywebview blocks selecting and copying by default
        )
        self._window.events.closing += self._on_closing

    def open(self, url: str) -> None:
        self._window.load_url(url)
        self._window.show()
        self._window.restore()

    def set_theme(self, theme: str) -> None:
        """Light, dark or the system's, applied to the open page at once."""
        script = (
            f"document.documentElement.dataset.theme = '{theme}'"
            if theme in ("light", "dark")
            else "delete document.documentElement.dataset.theme"
        )
        self._window.evaluate_js(script)

    def destroy(self) -> None:
        self._quitting = True
        self._window.destroy()

    def _on_closing(self) -> bool:
        if self._quitting:
            return True
        self._window.hide()
        return False  # keep it for the next click on the tray icon

    @staticmethod
    def start(icon: Path | None = None) -> None:
        """Run the window loop on the main thread until the tray quits. The icon
        (.ico) replaces Python's on the taskbar and the title bar."""
        import webview

        webview.start(private_mode=False, icon=str(icon) if icon else None)
