import json
import os
from utils.logger import get_logger
from config.paths import SETTINGS_FILE, ensure_runtime_layout

class Settings:
    def __init__(self):
        self.logger = get_logger("Settings")
        ensure_runtime_layout()
        self.path = SETTINGS_FILE
        self.defaults = {
            "threads": 10,
            "instagram_threads": 2,
            "timeout": 15,
            "webhook_url": "",
            "use_proxies": False,
            "jitter_min": 0.5,
            "jitter_max": 1.5,
            "mode": "safe",
            "retry_unknown_instagram": True,
            "platform_cache_ttl_hours": {
                "github": 24,
                "pinterest": 12,
                "instagram": 0
            },
            "platforms": {
                "pinterest": True,
                "instagram": True,
                "github": True
            }
        }
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return self.defaults.copy()
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                return self._deep_merge(self.defaults, loaded)
        except Exception:
            return self.defaults.copy()

    def _deep_merge(self, base, incoming):
        if not isinstance(base, dict) or not isinstance(incoming, dict):
            return incoming
        merged = dict(base)
        for key, value in incoming.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            self.logger.exception("settings_save_failed")

    def get(self, key, default=None):
        keys = key.split('.')
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def set(self, key, value):
        keys = key.split('.')
        target = self.data
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        self.save()

    def set_many(self, updates):
        for key, value in updates.items():
            keys = key.split('.')
            target = self.data
            for k in keys[:-1]:
                target = target.setdefault(k, {})
            target[keys[-1]] = value
        self.save()

settings = Settings()
