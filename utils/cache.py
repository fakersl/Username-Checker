import json
import os
import threading
from datetime import datetime, timedelta
from utils.logger import get_logger
from config.settings import settings
from config.paths import CACHE_FILE, ensure_runtime_layout

class ResultCache:
    def __init__(self, cache_file=None, ttl_hours=24, flush_interval=2):
        ensure_runtime_layout()
        self.cache_file = cache_file or CACHE_FILE
        self.ttl = timedelta(hours=ttl_hours)
        self.flush_interval = flush_interval
        self._lock = threading.RLock()
        self._dirty = False
        self._stop_event = threading.Event()
        self._logger = get_logger("ResultCache")
        self.cache = self._load()
        self._flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self._flush_thread.start()

    def _save_locked(self):
        try:
            parent = os.path.dirname(self.cache_file)
            if parent:
                os.makedirs(parent, exist_ok=True)
            tmp = f"{self.cache_file}.tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.cache_file)
            self._dirty = False
        except Exception:
            self._logger.exception("cache_save_failed")

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                self._logger.exception("cache_load_failed")
                return {}
        return {}

    def _flush_worker(self):
        while not self._stop_event.is_set():
            self._stop_event.wait(self.flush_interval)
            with self._lock:
                if self._dirty:
                    self._save_locked()

    def get(self, username, platform):
        key = f"{username}:{platform}"
        with self._lock:
            if key in self.cache:
                data = self.cache[key]
                ttl_map = settings.get("platform_cache_ttl_hours", {}) or {}
                ttl_hours = ttl_map.get(platform, self.ttl.total_seconds() / 3600)
                if ttl_hours <= 0:
                    return None
                platform_ttl = timedelta(hours=float(ttl_hours))
                if datetime.now() - datetime.fromisoformat(data['timestamp']) < platform_ttl:
                    return data['available']
        return None

    def set(self, username, platform, available):
        key = f"{username}:{platform}"
        with self._lock:
            self.cache[key] = {
                'available': available,
                'timestamp': datetime.now().isoformat()
            }
            self._dirty = True

    def flush(self):
        with self._lock:
            if self._dirty:
                self._save_locked()

    def close(self):
        self._stop_event.set()
        if self._flush_thread.is_alive():
            self._flush_thread.join(timeout=2)
        self.flush()
