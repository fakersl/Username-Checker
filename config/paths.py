import os

APP_DIR_NAME = "username checker"
APP_DIR = os.path.join(os.getcwd(), APP_DIR_NAME)
CONFIG_DIR = os.path.join(APP_DIR, "config")
DATA_DIR = os.path.join(APP_DIR, "data")
LOGS_DIR = os.path.join(APP_DIR, "logs")
EXPORTS_DIR = os.path.join(APP_DIR, "exports")
CACHE_DIR = os.path.join(APP_DIR, "cache")
PROXIES_DIR = os.path.join(APP_DIR, "proxies")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
DATABASE_FILE = os.path.join(DATA_DIR, "username_checker.db")
LOG_FILE = os.path.join(LOGS_DIR, "app.log")
CACHE_FILE = os.path.join(CACHE_DIR, "results.json")
PROXIES_FILE = os.path.join(PROXIES_DIR, "proxies.txt")
GOOD_PROXIES_FILE = os.path.join(PROXIES_DIR, "good_proxies.txt")
BAD_PROXIES_FILE = os.path.join(PROXIES_DIR, "bad_proxies.txt")


def _move_if_needed(src: str, dst: str):
    try:
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(src, dst)
    except Exception:
        pass


def _merge_dir(src: str, dst: str):
    try:
        if not os.path.isdir(src):
            return
        for root, _, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_root = dst if rel == "." else os.path.join(dst, rel)
            os.makedirs(target_root, exist_ok=True)
            for name in files:
                src_file = os.path.join(root, name)
                dst_file = os.path.join(target_root, name)
                if not os.path.exists(dst_file):
                    try:
                        os.replace(src_file, dst_file)
                    except Exception:
                        pass
    except Exception:
        pass


def ensure_runtime_layout():
    for path in (APP_DIR, CONFIG_DIR, DATA_DIR, LOGS_DIR, EXPORTS_DIR, CACHE_DIR, PROXIES_DIR):
        os.makedirs(path, exist_ok=True)
    for path in (SETTINGS_FILE, PROXIES_FILE, GOOD_PROXIES_FILE, BAD_PROXIES_FILE):
        if not os.path.exists(path):
            try:
                open(path, "a", encoding="utf-8").close()
            except Exception:
                pass
    legacy_map = {
        os.path.join(os.getcwd(), "config", "settings.json"): SETTINGS_FILE,
        os.path.join(os.getcwd(), "data", "username_checker.db"): DATABASE_FILE,
        os.path.join(os.getcwd(), "logs", "app.log"): LOG_FILE,
        os.path.join(os.getcwd(), "cache", "results.json"): CACHE_FILE,
        os.path.join(APP_DIR, "proxies.txt"): PROXIES_FILE,
        os.path.join(APP_DIR, "good_proxies.txt"): GOOD_PROXIES_FILE,
        os.path.join(APP_DIR, "bad_proxies.txt"): BAD_PROXIES_FILE,
    }
    for src, dst in legacy_map.items():
        _move_if_needed(src, dst)
    _merge_dir(os.path.join(os.getcwd(), "exports"), EXPORTS_DIR)
    _merge_dir(os.path.join(os.getcwd(), "logs"), LOGS_DIR)
    _merge_dir(os.path.join(os.getcwd(), "cache"), CACHE_DIR)
    _merge_dir(os.path.join(os.getcwd(), "data"), DATA_DIR)
