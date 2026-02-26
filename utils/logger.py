import logging
import os
from logging.handlers import RotatingFileHandler
from config.paths import LOGS_DIR, LOG_FILE, ensure_runtime_layout


_configured = False


def setup_logger():
    global _configured
    if _configured:
        return
    ensure_runtime_layout()
    os.makedirs(LOGS_DIR, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8"
        )
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    _configured = True


def get_logger(name: str):
    setup_logger()
    return logging.getLogger(name)
