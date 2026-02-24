# utils/cache.py
import json
import os
from datetime import datetime, timedelta

class ResultCache:
    def __init__(self, cache_file="cache/results.json", ttl_hours=24):
        self.cache_file = cache_file
        self.ttl = timedelta(hours=ttl_hours)
        self.cache = self._load()

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def get(self, username, platform):
        key = f"{username}:{platform}"
        if key in self.cache:
            data = self.cache[key]
            if datetime.now() - datetime.fromisoformat(data['timestamp']) < self.ttl:
                return data['available']
        return None

    def set(self, username, platform, available):
        key = f"{username}:{platform}"
        self.cache[key] = {
            'available': available,
            'timestamp': datetime.now().isoformat()
        }
        self._save()