import os
import sys
import ctypes
import threading
from gui.app_window import AppWindow
from utils.logger import get_logger
from config.paths import ensure_runtime_layout

logger = get_logger("main")

def _validate_startup_proxies():
    try:
        from core.proxy_checker import load_proxies, check_proxies
        from core.platforms import ProxyManager

        pm = ProxyManager()
        proxies = load_proxies(pm.proxies_file)
        if proxies:
            def _worker():
                try:
                    check_proxies(proxies, workers=min(50, max(5, len(proxies))))
                except Exception:
                    logger.exception("startup_proxy_check_failed")

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
    except Exception:
        logger.exception("startup_proxy_validation_failed")

def configure_environment():
    ensure_runtime_layout()
    if sys.platform == 'darwin':
        os.environ.setdefault('TK_SILENCE_DEPRECATION', '1')
    if sys.platform.startswith('linux'):
        os.environ.setdefault('GTK_THEME', 'Adwaita:dark')
    if sys.platform.startswith('win'):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            logger.exception("dpi_awareness_failed")
            
    try:
        ensure_runtime_layout()
    except Exception:
        logger.exception("support_files_creation_failed")


def run_startup_healthcheck():
    status = {
        "settings_ok": False,
        "db_ok": False,
        "proxies_file_ok": False,
        "proxy_count": 0
    }
    try:
        from config.settings import settings
        settings.load()
        status["settings_ok"] = True
    except Exception:
        logger.exception("healthcheck_settings_failed")
    try:
        from utils.database import db
        db.get_statistics(1)
        status["db_ok"] = True
    except Exception:
        logger.exception("healthcheck_db_failed")
    try:
        from core.platforms import ProxyManager
        pm = ProxyManager()
        status["proxies_file_ok"] = os.path.exists(pm.proxies_file)
        status["proxy_count"] = len(pm.proxies)
    except Exception:
        logger.exception("healthcheck_proxy_failed")
    logger.info("healthcheck=%s", status)
    return status

if __name__ == "__main__":
    configure_environment()
    run_startup_healthcheck()
    _validate_startup_proxies()
    app = AppWindow()
    app.run()
