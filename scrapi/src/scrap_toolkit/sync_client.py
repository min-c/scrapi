import time
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import settings

class SyncClient:
    def __init__(self, rate_per_sec: float = None):
        self.session = requests.Session()
        retries = Retry(
            total=settings.max_retries,
            backoff_factor=settings.backoff_factor,
            status_forcelist=[400, 402, 429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET","POST","PUT","DELETE","HEAD","OPTIONS","PATCH"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"User-Agent": settings.user_agent, "Accept": "*/*"})
        self.rate_per_sec = rate_per_sec or settings.rate_per_sec
        self._last_request = 0.0

    def _rate_limit(self):
        if self.rate_per_sec <= 0:
            return
        min_interval = 1.0 / self.rate_per_sec
        now = time.time()
        sleep_for = min_interval - (now - self._last_request)
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last_request = time.time()

    def get(self, url: str, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str,str]]=None, timeout: Optional[float]=None) -> requests.Response:
        self._rate_limit()
        return self.session.get(url, params=params, headers=headers, timeout=timeout or settings.timeout)

    def post(self, url: str, *, data=None, json=None, headers: Optional[Dict[str,str]]=None, timeout: Optional[float]=None) -> requests.Response:
        self._rate_limit()
        return self.session.post(url, data=data, json=json, headers=headers, timeout=timeout or settings.timeout)

    def close(self):
        self.session.close()
