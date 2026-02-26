from typing import Optional
import platform
from utils.logger import get_logger
try:
    if platform.system() == 'Windows':
        from win10toast import ToastNotifier
        NOTIFICATIONS_AVAILABLE = True
    else:
        NOTIFICATIONS_AVAILABLE = False
except ImportError:
    NOTIFICATIONS_AVAILABLE = False


class NotificationManager:
    def __init__(self):
        self.logger = get_logger("NotificationManager")
        self.toaster = None
        if NOTIFICATIONS_AVAILABLE:
            try:
                self.toaster = ToastNotifier()
            except Exception:
                self.toaster = None

    def notify(self, title: str, message: str, level: str = "info", duration: int = 7, icon_path: Optional[str] = None) -> bool:
        return self.send(title, message, duration=duration, icon_path=icon_path)

    def send(self, title: str, message: str, duration: int = 5, icon_path: Optional[str] = None) -> bool:
        if not self.toaster:
            return False
        try:
            self.toaster.show_toast(
                title,
                message,
                duration=duration,
                icon_path=icon_path,
                threaded=True
            )
            return True
        except Exception:
            self.logger.exception("notification_send_failed")
            return False

    def notify_username_available(self, username: str, platforms: list) -> bool:
        platforms_str = ", ".join([p.upper() for p in platforms])
        return self.send(
            "Username Available!",
            f"@{username}\nAvailable on: {platforms_str}",
            duration=10
        )


notification_manager = NotificationManager()
