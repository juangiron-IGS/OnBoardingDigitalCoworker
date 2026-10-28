"""The Coworker window the tray opens: the web app itself (chat, inbox, approval,
dashboard, status, knowledge) in a compact desktop window docked above the clock,
like a chat popup. Same pages and same controls as the browser, so every approval
still goes through the web app's governance (BR-002)."""

import ctypes
import sys
from pathlib import Path

# The window takes 25% of the screen's width and 90% of its height.
WIDTH_SHARE, HEIGHT_SHARE = 0.25, 0.90
MIN_WIDTH, MIN_HEIGHT = 300, 480
MARGIN, TASKBAR = 12, 48
# Window styles: a fixed window has no minimize or maximize box and no resize edge.
GWL_STYLE, WS_THICKFRAME, WS_MINIMIZEBOX, WS_MAXIMIZEBOX = (
    -16,
    0x40000,
    0x20000,
    0x10000,
)
SWP_FRAMECHANGED_ONLY = 0x0001 | 0x0002 | 0x0004 | 0x0020  # no size, move or z-order


def window_size(screen_width: int, screen_height: int) -> tuple[int, int]:
    """Width and height for this screen, kept above the taskbar."""
    width = max(MIN_WIDTH, round(screen_width * WIDTH_SHARE))
    room = screen_height - TASKBAR - 2 * MARGIN
    height = max(MIN_HEIGHT, min(round(screen_height * HEIGHT_SHARE), room))
    return width, height


def docked(
    screen_width: int, screen_height: int, width: int, height: int
) -> tuple[int, int]:
    """Top-left corner that docks the window at the bottom right, above the taskbar."""
    x = max(0, screen_width - width - MARGIN)
    y = max(0, screen_height - height - TASKBAR - MARGIN)
    return x, y


def primary(screens: list):  # noqa: ANN201 - a pywebview Screen, or None
    """The main screen (at 0,0); pywebview may list another monitor first."""
    return next(
        (s for s in screens if getattr(s, "x", 0) == 0 and getattr(s, "y", 0) == 0),
        screens[0] if screens else None,
    )


class CoworkerWindow:
    """One pywebview window, created hidden and shown on demand. Closing it only
    hides it; it is destroyed when the tray quits. With a fixed width (the default)
    it has no minimize, maximize or resize edge, and any size change springs back;
    otherwise its width can be dragged and only the height stays fixed."""

    def __init__(self, url: str, fixed: bool = True) -> None:
        import webview  # the GUI toolkit loads only when the window is used

        screen = primary(webview.screens)
        self._screen = (screen.width, screen.height) if screen else (1920, 1080)
        self._size = window_size(*self._screen)
        x, y = docked(*self._screen, *self._size)
        self.fixed = fixed
        self._quitting = False
        self._window = webview.create_window(
            "Onboarding Coworker",
            url,
            width=self._size[0],
            height=self._size[1],
            x=x,
            y=y,
            min_size=(MIN_WIDTH, MIN_HEIGHT),
            hidden=True,
            text_select=True,  # pywebview blocks selecting and copying by default
        )
        self._window.events.closing += self._on_closing
        self._window.events.resized += self._on_resized
        self._window.events.shown += self._apply_frame

    def set_fixed(self, fixed: bool) -> None:
        """Fixed width (25% of the screen) or a width the person drags."""
        self.fixed = fixed
        self._apply_frame()
        if fixed:
            self._snap(self._size[0])

    def _apply_frame(self) -> None:
        """Fixed: only the close button and no resize edge. Free: all of them."""
        if sys.platform != "win32" or self._window.native is None:
            return
        user32 = ctypes.windll.user32
        hwnd = self._window.native.Handle.ToInt64()
        boxes = WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style = style & ~boxes if self.fixed else style | boxes
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FRAMECHANGED_ONLY)

    def _on_resized(self, width: int, height: int) -> None:
        wanted = self._size[0] if self.fixed else width
        if (width, height) != (wanted, self._size[1]):
            self._snap(wanted)

    def _snap(self, width: int) -> None:
        """Back to the fixed height (and width), docked above the clock."""
        self._window.resize(width, self._size[1])
        self._window.move(*docked(*self._screen, width, self._size[1]))

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
