import requests
import random
import time
import os
import importlib.util
from abc import ABC, abstractmethod
from config.settings import settings
from config.paths import PROXIES_FILE, BAD_PROXIES_FILE, ensure_runtime_layout

_instagram_session_cookie = ""
_blacklist_pending = set()
_blacklist_pending_count = 0

def _normalize_instagram_session_cookie(cookie: str) -> str:
    if not cookie:
        return ""
    value = cookie.strip().strip('"').strip("'")
    if not value:
        return ""

    parts = [part.strip() for part in value.split(";") if part.strip()]
    for part in parts:
        if part.lower().startswith("sessionid="):
            value = part.split("=", 1)[1].strip()
            break
    else:
        if value.lower().startswith("sessionid="):
            value = value.split("=", 1)[1].strip()

    return value.strip().strip('"').strip("'")

def set_instagram_session_cookie(cookie: str):
    global _instagram_session_cookie
    _instagram_session_cookie = _normalize_instagram_session_cookie(cookie)

def get_instagram_session_cookie() -> str:
    return _instagram_session_cookie

class ProxyManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyManager, cls).__new__(cls)
            cls._instance.proxies = []
            cls._instance.blacklist = set()
            cls._instance.rate_limited_until = {}
            cls._instance.last_proxy_selected = None

            ensure_runtime_layout()
            cls._instance.proxies_file = PROXIES_FILE
            cls._instance.blacklist_file = BAD_PROXIES_FILE
            for p in (cls._instance.proxies_file, cls._instance.blacklist_file):
                try:
                    open(p, 'a', encoding='utf-8').close()
                except Exception:
                    pass

            cls._instance.socks_supported = importlib.util.find_spec('socks') is not None
            cls._instance.load_proxies()
            cls._instance.load_blacklist()
        return cls._instance

    def load_proxies(self):
        if os.path.exists(self.proxies_file):
            try:
                with open(self.proxies_file, "r", encoding="utf-8") as f:
                    self.proxies = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            except:
                self.proxies = []

    def save_proxies(self, path: str = None):
        try:
            path = path or self.proxies_file
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.proxies))
        except:
            pass

    def load_blacklist(self, path: str = None):
        path = path or self.blacklist_file
        self.blacklist = set()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.blacklist = set([line.strip() for line in f if line.strip()])
            except:
                self.blacklist = set()

    def save_blacklist(self, path: str = None):
        path = path or self.blacklist_file
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(self.blacklist)))
        except:
            pass

    def mark_bad_proxy(self, proxy: str):
        global _blacklist_pending, _blacklist_pending_count
        if not proxy: return
        self.blacklist.add(proxy.strip())
        _blacklist_pending.add(proxy.strip())
        _blacklist_pending_count += 1
        if _blacklist_pending_count >= 20:
            self.save_blacklist()
            _blacklist_pending.clear()
            _blacklist_pending_count = 0

    def unmark_bad_proxy(self, proxy: str):
        try:
            self.blacklist.discard(proxy.strip())
            self.save_blacklist()
        except:
            pass

    def is_blacklisted(self, proxy: str) -> bool:
        return proxy.strip() in self.blacklist

    def mark_rate_limited_proxy(self, proxy: str, cooldown_seconds: int = 300):
        if not proxy:
            return
        self.rate_limited_until[proxy.strip()] = time.time() + max(30, int(cooldown_seconds))

    def is_rate_limited_proxy(self, proxy: str) -> bool:
        if not proxy:
            return False
        until = self.rate_limited_until.get(proxy.strip())
        if not until:
            return False
        if time.time() >= until:
            self.rate_limited_until.pop(proxy.strip(), None)
            return False
        return True
    
    def flush_blacklist(self):
        global _blacklist_pending_count
        if _blacklist_pending_count > 0:
            self.save_blacklist()
            _blacklist_pending_count = 0

    def clear_blacklist(self):
        self.blacklist = set()
        self.save_blacklist()

    def add_proxy(self, proxy: str, path: str = None) -> bool:
        if not proxy: return False
        p = proxy.strip()
        if not p or p in self.proxies:
            return False
        self.proxies.append(p)
        self.save_proxies(path or self.proxies_file)
        return True

    def remove_proxy(self, proxy: str, path: str = None) -> bool:
        if not proxy: return False
        p = proxy.strip()
        try:
            self.proxies.remove(p)
            self.save_proxies(path or self.proxies_file)
            return True
        except ValueError:
            return False

    def get_proxy(self):
        if not settings.get("use_proxies") or not self.proxies:
            self.last_proxy_selected = None
            return None

        available = [
            p for p in self.proxies
            if p and p.strip() and p.strip() not in self.blacklist and not self.is_rate_limited_proxy(p.strip())
        ]
        if not available:
            self.last_proxy_selected = None
            return None

        proxy = random.choice(available).strip()
        self.last_proxy_selected = proxy

        if proxy.startswith("http://") or proxy.startswith("https://") or proxy.startswith("socks"):
            scheme_host = proxy
        else:
            scheme_host = f"http://{proxy}"

        if scheme_host.startswith("socks") and not self.socks_supported:
            self.mark_bad_proxy(proxy)
            return None

        return {
            "http": scheme_host,
            "https": scheme_host
        }

class PlatformChecker(ABC):
    _base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    }
    _user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.proxy_mgr = ProxyManager()
        self.last_proxy_raw = None

    def get_request_kwargs(self):
        headers = self._base_headers.copy()
        headers['User-Agent'] = random.choice(self._user_agents)
        kwargs = {
            "headers": headers,
            "timeout": settings.get("timeout") or 10
        }
        
        proxy = self.proxy_mgr.get_proxy()
        if proxy:
            kwargs["proxies"] = proxy
            self.last_proxy_raw = self.proxy_mgr.last_proxy_selected
        else:
            self.last_proxy_raw = None
            
        return kwargs

    def jitter(self):
        pass

    @abstractmethod
    def check(self, username):
        pass

class PinterestChecker(PlatformChecker):
    def check(self, username):
        url = f"https://www.pinterest.com/{username}/"
        try:
            kwargs = self.get_request_kwargs()
            response = self.session.get(url, **kwargs)
            
            if response.url.rstrip('/') in ["https://www.pinterest.com", "https://br.pinterest.com"]:
                if len(username) < 4:
                    return "POSSIBLY_AVAILABLE"
                return True
                
            if response.status_code == 404:
                if len(username) < 4:
                    return "POSSIBLY_AVAILABLE"
                return True
            
            content = response.text.lower()
            if "page not found" in content:
                if len(username) < 4:
                    return "POSSIBLY_AVAILABLE"
                return True
                
            return False
        except:
            return False

class GitHubChecker(PlatformChecker):
    def check(self, username):
        url = f"https://github.com/{username}"
        try:
            kwargs = self.get_request_kwargs()
            response = self.session.get(url, **kwargs)
            
            if response.status_code == 404:
                if len(username) < 4:
                    return "POSSIBLY_AVAILABLE"
                return True
                
            return False
        except:
            return False

class InstagramChecker(PlatformChecker):
    def __init__(self):
        super().__init__()
        self.rate_limit_penalty = 1.0

    def jitter(self):
        min_delay = float(settings.get("jitter_min") or 0.1)
        max_delay = float(settings.get("jitter_max") or 0.5)
        mode = (settings.get("mode") or "safe").lower()
        mode_factor = 1.3 if mode == "safe" else 0.8
        min_wait = min_delay * self.rate_limit_penalty * mode_factor
        max_wait = max_delay * self.rate_limit_penalty * mode_factor
        if max_wait < min_wait:
            max_wait = min_wait
        time.sleep(random.uniform(min_wait, max_wait))

    def _on_rate_limit(self):
        self.rate_limit_penalty = min(4.0, self.rate_limit_penalty * 1.35)
        if self.last_proxy_raw:
            self.proxy_mgr.mark_rate_limited_proxy(self.last_proxy_raw, cooldown_seconds=420)

    def _on_success(self):
        self.rate_limit_penalty = max(1.0, self.rate_limit_penalty * 0.95)

    def _request_kwargs(self):
        kwargs = self.get_request_kwargs()
        headers = kwargs.get("headers", {}).copy()
        headers["X-IG-App-ID"] = "936619743392459"
        headers["Referer"] = "https://www.instagram.com/"
        headers["X-Requested-With"] = "XMLHttpRequest"
        kwargs["headers"] = headers
        return kwargs

    def _check_profile_info(self, username):
        kwargs = self._request_kwargs()
        response = self.session.get(
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
            **kwargs
        )
        if response.status_code == 429:
            return "RATE_LIMIT", 0, 0
        if response.status_code in (401, 403):
            return "BLOCKED", 0, 0
        if response.status_code == 404:
            return "OK", 4, 0
        if response.status_code == 200:
            try:
                data = response.json()
                user = data.get("data", {}).get("user")
                if isinstance(user, dict):
                    if user.get("username", "").lower() == username:
                        return "OK", 0, 5
                    return "OK", 0, 0
                if user is None:
                    return "OK", 3, 0
            except Exception:
                return "OK", 0, 0
        return "OK", 0, 0

    def _check_topsearch_signal(self, username):
        kwargs = self._request_kwargs()
        response = self.session.get(
            "https://www.instagram.com/web/search/topsearch/",
            params={"context": "blended", "query": username, "count": "30"},
            **kwargs
        )
        if response.status_code == 429:
            return "RATE_LIMIT", 0, 0
        if response.status_code in (401, 403):
            return "BLOCKED", 0, 0
        if response.status_code != 200:
            return "OK", 0, 0
        try:
            data = response.json()
            users = data.get("users", [])
            if not isinstance(users, list):
                return "OK", 0, 0
            for item in users:
                found = item.get("user", {}).get("username", "").lower()
                if found == username:
                    return "OK", 0, 4
            return "OK", 1, 0
        except Exception:
            return "OK", 0, 0

    def _check_html_profile(self, username):
        kwargs = self._request_kwargs()
        response = self.session.get(f"https://www.instagram.com/{username}/", **kwargs)
        if response.status_code == 429:
            return "RATE_LIMIT", 0, 0
        if response.status_code in (401, 403):
            return "BLOCKED", 0, 0
        if response.status_code == 404:
            return "OK", 2, 0
        if response.status_code != 200:
            return "OK", 0, 0
        content = response.text.lower()
        taken_score = 0
        available_score = 0
        if "page isn't available" in content or "page not found" in content:
            available_score += 2
        return "OK", available_score, taken_score

    def check(self, username):
        self.jitter()
        username = username.lower().strip()
        if not username or len(username) < 1 or len(username) > 30:
            return False
        self._setup_instagram_session()
        has_session = bool(get_instagram_session_cookie())

        available_score = 0
        taken_score = 0

        try:
            state, avail, taken = self._check_profile_info(username)
            if state == "RATE_LIMIT":
                self._on_rate_limit()
                return "RATE_LIMIT"
            if state == "BLOCKED":
                return None
            available_score += avail
            taken_score += taken
        except Exception:
            pass

        try:
            state, avail, taken = self._check_topsearch_signal(username)
            if state == "RATE_LIMIT":
                self._on_rate_limit()
                return "RATE_LIMIT"
            if state == "BLOCKED":
                return None
            available_score += avail
            taken_score += taken
        except Exception:
            pass

        try:
            state, avail, taken = self._check_html_profile(username)
            if state == "RATE_LIMIT":
                self._on_rate_limit()
                return "RATE_LIMIT"
            if state == "BLOCKED":
                return None
            available_score += avail
            taken_score += taken
        except Exception:
            pass

        if len(username) < 5:
            if has_session and taken_score >= 4:
                return False
            if not has_session and taken_score >= 8:
                return False
            if taken_score > 0 and not has_session:
                return None
            if available_score >= 8:
                self._on_success()
                return True
            if available_score >= 4:
                return "POSSIBLY_AVAILABLE"
            return None

        if has_session and taken_score >= 4:
            self._on_success()
            return False
        if not has_session and taken_score >= 8:
            self._on_success()
            return False
        if available_score >= 4 and taken_score == 0:
            self._on_success()
            return True
        if available_score >= 2 and taken_score == 0:
            if len(username) >= 5:
                return True
            return "POSSIBLY_AVAILABLE"
        if not has_session and taken_score > 0:
            return None
        return None

    def validate_session_cookie(self):
        cookie = get_instagram_session_cookie()
        if not cookie:
            return False
        self._setup_instagram_session()
        try:
            kwargs = self._request_kwargs()
            kwargs.pop("proxies", None)
            response = self.session.get(
                "https://www.instagram.com/api/v1/accounts/current_user/?edit=true",
                allow_redirects=False,
                **kwargs
            )
            if response.status_code == 200:
                data = response.json()
                user = data.get("user") or data.get("logged_in_user")
                if isinstance(user, dict) and user.get("pk"):
                    return True

            fallback_kwargs = kwargs.copy()
            fallback_kwargs["allow_redirects"] = False
            fallback = self.session.get("https://www.instagram.com/accounts/edit/", **fallback_kwargs)
            if fallback.status_code == 200 and "/accounts/login" not in fallback.url.lower():
                return True

            location = (fallback.headers.get("Location") or "").lower()
            if "/accounts/login" in location:
                return False

            return False
        except Exception:
            return False

    def _setup_instagram_session(self):
        cookie = get_instagram_session_cookie()
        for existing in list(self.session.cookies):
            if existing.name == "sessionid" and "instagram.com" in (existing.domain or ""):
                try:
                    self.session.cookies.clear(domain=existing.domain, path=existing.path, name=existing.name)
                except Exception:
                    pass
        if cookie and cookie.strip():
            self.session.cookies.set("sessionid", cookie, domain="instagram.com", path="/")
            self.session.cookies.set("sessionid", cookie, domain=".instagram.com", path="/")
            self.session.cookies.set("sessionid", cookie, domain="www.instagram.com", path="/")
