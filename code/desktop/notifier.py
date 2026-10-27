"""Windows notifications for the Coworker Tray, with the Coworker's name and logo.

Windows shows a notification under the app that sends it. The tray registers
itself once for the current user (HKCU, no admin rights) as "Onboarding
Coworker" with its logo, so the notification says that instead of "Python".
A click on the notification, or on its "Open case" button, opens the Coworker
window on the alert's case. Without windows-toasts (or outside Windows) the
tray falls back to the plain notification of its icon.
"""

import os
import sys
from collections.abc import Callable
from pathlib import Path

AUMID = "INSPYR.OnboardingCoworker"
APP_NAME = "Onboarding Coworker"
BRAND = "1F5FAE"  # the tile colour behind the logo in Windows' notification header


def logo_path() -> Path:
    """Where the logo PNG is kept for Windows (per user, outside the repository)."""
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "OnboardingCoworker"
    base.mkdir(parents=True, exist_ok=True)
    return base / "coworker-logo.png"


def register_app(logo: Path) -> None:
    """Register the tray's name and logo for its notifications (current user)."""
    import winreg

    key = rf"Software\Classes\AppUserModelId\{AUMID}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as handle:
        winreg.SetValueEx(handle, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(handle, "IconUri", 0, winreg.REG_SZ, str(logo))
        winreg.SetValueEx(handle, "IconBackgroundColor", 0, winreg.REG_SZ, BRAND)


def headline(alert: dict, more: int) -> tuple[str, str]:
    """(title, body) of the notification; the title names the case."""
    case = alert.get("case_id") or "Onboarding"
    extra = f"  (+{more} more)" if more else ""
    return f"New alert · {case}", alert["text"] + extra


class Notifier:
    """Shows one notification per poll: the newest alert, with how many more."""

    def __init__(
        self,
        logo: Path,
        on_open: Callable[[str | None], None],
        fallback: Callable[[str, str], None],
    ) -> None:
        self._logo = logo
        self._on_open = on_open
        self._fallback = fallback
        self._toaster = None
        if sys.platform != "win32":
            return
        try:
            from windows_toasts import InteractableWindowsToaster

            register_app(logo)
            self._toaster = InteractableWindowsToaster(APP_NAME, AUMID)
        except Exception:  # noqa: BLE001 - the plain notification still works
            self._toaster = None

    def show(self, alert: dict, more: int, role_label: str) -> None:
        title, body = headline(alert, more)
        if self._toaster is None:
            self._fallback(body, title)
            return
        from windows_toasts import (
            Toast,
            ToastButton,
            ToastDisplayImage,
            ToastImagePosition,
        )

        case_id = alert.get("case_id")
        toast = Toast([title, body])
        toast.attribution_text = f"For {role_label}"
        toast.AddImage(
            ToastDisplayImage.fromPath(
                str(self._logo), position=ToastImagePosition.AppLogo
            )
        )
        toast.AddAction(ToastButton("Open case", arguments=f"open:{case_id or ''}"))
        toast.on_activated = lambda _event: self._on_open(case_id)
        try:
            self._toaster.show_toast(toast)
        except Exception:  # noqa: BLE001 - never lose an alert to a toast error
            self._fallback(body, title)
