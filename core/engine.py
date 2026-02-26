import concurrent.futures
import requests
import threading
from datetime import datetime
from queue import Queue
from core.platforms import PinterestChecker, GitHubChecker, InstagramChecker, ProxyManager
from core.validation import Validator
from config.settings import settings
from utils.cache import ResultCache
from utils.logger import get_logger


class AuditEngine:
    def __init__(self):
        self.logger = get_logger("AuditEngine")
        self.checkers = {
            "pinterest": PinterestChecker(),        
            "github": GitHubChecker(),
            "instagram": InstagramChecker()
        }
        self.validator = Validator()
        self.cache = ResultCache()
        self.executor = None
        self.active = False
        self.monitor_mode = False
        self.settings_data = settings.load()
        self.webhook_queue = Queue()
        self.webhook_thread = threading.Thread(target=self._webhook_worker, daemon=True)
        self.webhook_thread.start()
        self.monitor_event = threading.Event()
        self.instagram_semaphore = threading.Semaphore(max(1, int(settings.get("instagram_threads") or 2)))

    def refresh_settings(self):
        self.settings_data = settings.load()
        self.instagram_semaphore = threading.Semaphore(max(1, int(settings.get("instagram_threads") or 2)))


    def check_target(self, username, settings_data=None):
        if not self.active:
            return None

        if settings_data is None:
            settings_data = self.settings_data
        result = {
            "username": username,
            "available_on": [],
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "checked_platforms": [],
            "platform_status": {}
        }

        platforms_to_check = []
        try:
            if settings_data.get("platforms", {}).get("pinterest") and self.validator.check_pinterest(username):
                platforms_to_check.append("pinterest")
        except Exception:
            pass
        try:
            if settings_data.get("platforms", {}).get("github") and self.validator.check_github(username):
                platforms_to_check.append("github")
        except Exception:
            pass
        try:
            if settings_data.get("platforms", {}).get("instagram") and self.validator.check_instagram(username):
                platforms_to_check.append("instagram")
        except Exception:
            pass



        if not platforms_to_check:
            return result

        result["checked_platforms"] = platforms_to_check
        result["possibly_available"] = []

        for platform in platforms_to_check[:]:
            if platform == "instagram":
                continue
            cached = self.cache.get(username, platform)
            if cached is not None:
                platforms_to_check.remove(platform)
            if cached == "POSSIBLY_AVAILABLE":
                result["possibly_available"].append(platform)
            elif cached is True:
                result["available_on"].append(platform)

        for platform in platforms_to_check:
            try:
                if platform == "instagram":
                    with self.instagram_semaphore:
                        check_result = self.checkers[platform].check(username)
                else:
                    check_result = self.checkers[platform].check(username)
                if check_result == "RATE_LIMIT":
                    result["available_on"].append(f"RATE_LIMIT:{platform}")
                    result["platform_status"][platform] = "rate_limit"
                    break
                if platform != "instagram":
                    self.cache.set(username, platform, check_result)
                if check_result == "POSSIBLY_AVAILABLE":
                    result["possibly_available"].append(platform)
                    result["platform_status"][platform] = "possibly_available"
                elif check_result is True:
                    result["available_on"].append(platform)
                    result["platform_status"][platform] = "available"
                else:
                    if check_result is None and len(username) < 4:
                        result["possibly_available"].append(platform)
                        result["platform_status"][platform] = "possibly_available"
                    elif check_result is False:
                        result["platform_status"][platform] = "taken"
                    elif check_result is None:
                        result["platform_status"][platform] = "unknown"
                        if platform == "instagram" and settings_data.get("retry_unknown_instagram", True):
                            retry_result = self.checkers[platform].check(username)
                            if retry_result is True:
                                result["available_on"].append(platform)
                                result["platform_status"][platform] = "available"
                            elif retry_result == "POSSIBLY_AVAILABLE":
                                result["possibly_available"].append(platform)
                                result["platform_status"][platform] = "possibly_available"
                            elif retry_result is False:
                                result["platform_status"][platform] = "taken"
            except Exception as e:
                self.logger.exception("platform_check_failed username=%s platform=%s", username, platform)
                continue

        if result["available_on"] or result["possibly_available"]:
            self.webhook_queue.put(result)

        return result
    
    def _webhook_worker(self):
        while True:
            try:
                data = self.webhook_queue.get(timeout=1)
                self._send_webhook(data)
            except:
                pass
    
    def _send_webhook(self, data):
        url = settings.get("webhook_url")
        if not url:
            return

        valid_platforms = {"instagram", "pinterest", "github"}
        available = [p for p in data.get("available_on", []) if p in valid_platforms]
        possibly_available = [p for p in data.get("possibly_available", []) if p in valid_platforms]
        
        all_available = available + possibly_available
        if not all_available:
            return

        links_text = ""
        for platform in all_available:
            if platform.lower() == "instagram":
                links_text += f"[Instagram](https://instagram.com/{data['username']})\n"
            elif platform.lower() == "pinterest":
                links_text += f"[Pinterest](https://pinterest.com/{data['username']})\n"
            elif platform.lower() == "github":
                links_text += f"[GitHub](https://github.com/{data['username']})\n"

        if available:
            title = f"Available: @{data['username']}"
            color = 0x22c55e
        else:
            title = f"Possibly Available (Verify): @{data['username']}"
            color = 0xf59e0b

        embed = {
            "title": f"{title} | by @00ie",
            "color": color,
            "fields": [
                {"name": "Username", "value": f"`@{data['username']}`", "inline": False},
                {"name": "Found at", "value": f"`{data['timestamp']}`", "inline": False},
                {"name": "Platform", "value": ", ".join([p.title() for p in all_available]), "inline": True},
                {"name": "Profile Link", "value": links_text, "inline": True}
            ],
            "footer": {
                "text": "github: @00ie | discord.gg/2asv4rEhGh"
            },
            "thumbnail": {
                "url": "https://i.pinimg.com/736x/91/2b/de/912bdecda7aca1f1aff51f022bbce8ca.jpg"
            }
        }

        payload = {
            "username": "Gon's Sniper",
            "avatar_url": "https://i.pinimg.com/736x/91/2b/de/912bdecda7aca1f1aff51f022bbce8ca.jpg",
            "embeds": [embed]
        }

        proxy_mgr = ProxyManager()
        proxies = proxy_mgr.get_proxy()
        attempts = []
        if proxies:
            attempts.append({"proxies": proxies})
        attempts.append({})
        for kwargs in attempts:
            try:
                response = requests.post(url, json=payload, timeout=8, **kwargs)
                if response.status_code < 400:
                    return
            except Exception:
                continue
        self.logger.error("webhook_send_failed")

    def start_bulk(self, usernames, callback):
        self.active = True
        self.monitor_mode = False
        self.refresh_settings()
        max_workers = int(settings.get("threads") or 10)
        normalized = []
        seen = set()
        for u in usernames:
            x = (u or "").strip().lower()
            if not x or x in seen:
                continue
            seen.add(x)
            normalized.append(x)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            self.executor = executor
            futures = {executor.submit(self.check_target, user, self.settings_data): user for user in normalized}

            for future in concurrent.futures.as_completed(futures):
                if not self.active:
                    break
                try:
                    data = future.result()
                    if data:
                        callback(data)
                except Exception:
                    pass

    def start_monitor(self, username, callback, delay=60):
        self.active = True
        self.monitor_mode = True
        self.refresh_settings()
        self.monitor_event.clear()

        while self.active:
            data = self.check_target(username, self.settings_data)
            if data:
                callback(data)

            self.monitor_event.wait(timeout=delay)

    def stop(self):
        self.active = False
        if self.executor:
            self.executor.shutdown(wait=False)
        self.cache.flush()
        proxy_mgr = ProxyManager()
        proxy_mgr.flush_blacklist()

    def close(self):
        self.stop()
        self.cache.close()
