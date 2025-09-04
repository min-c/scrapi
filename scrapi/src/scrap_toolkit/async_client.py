import asyncio
from typing import Optional, Dict, Any
import httpx
from .config import settings

class AsyncClient:
    def __init__(self, rate_per_sec: float = None):
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        self.client = httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent, "Accept": "*/*"},
            timeout=settings.timeout,
            limits=limits,
            http2=True,
        )
        self.rate_per_sec = rate_per_sec or settings.rate_per_sec
        self._sema = asyncio.Semaphore(int(self.rate_per_sec) if self.rate_per_sec >= 1 else 1)
        self._min_interval = 1.0 / max(self.rate_per_sec, 1e-6)
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def _rate_limit(self):
        async with self._sema:
            async with self._lock:
                now = asyncio.get_event_loop().time()
                wait = self._min_interval - (now - self._last)
                if wait > 0:
                    await asyncio.sleep(wait)
                self._last = asyncio.get_event_loop().time()

    async def get(self, url: str, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str,str]]=None) -> httpx.Response:
        await self._rate_limit()
        return await self.client.get(url, params=params, headers=headers)

    async def post(self, url: str, *, data=None, json=None, headers: Optional[Dict[str,str]]=None) -> httpx.Response:
        await self._rate_limit()
        return await self.client.post(url, data=data, json=json, headers=headers)

    async def aclose(self):
        await self.client.aclose()
