import threading
import time
from typing import Iterable, List, Optional

import requests
from django.conf import settings


class ProxyPool:
    """
    Minimal round-robin proxy pool with cooldowns.
    We mark a proxy as cooling off after failures/blocked responses so the next
    attempt uses a different exit IP.
    """

    def __init__(
        self,
        proxies: Iterable[str],
        cooldown_seconds: int = 60,
        max_failures: int = 3,
        retry_statuses: Optional[Iterable[int]] = None,
    ):
        self._proxies: List[dict] = [
            {"url": proxy.strip(), "cool_until": 0.0, "failures": 0}
            for proxy in proxies
            if proxy and proxy.strip()
        ]
        self._idx = 0
        self._lock = threading.Lock()
        self.cooldown_seconds = cooldown_seconds
        self.max_failures = max_failures
        self.retry_statuses = set(retry_statuses or [])

    def __len__(self):
        return len(self._proxies)

    def next_proxy(self) -> Optional[str]:
        if not self._proxies:
            return None
        now = time.time()
        with self._lock:
            for _ in range(len(self._proxies)):
                candidate = self._proxies[self._idx]
                self._idx = (self._idx + 1) % len(self._proxies)
                if candidate["cool_until"] <= now:
                    return candidate["url"]
            return None

    def _find(self, proxy_url: Optional[str]) -> Optional[dict]:
        if not proxy_url:
            return None
        for proxy in self._proxies:
            if proxy["url"] == proxy_url:
                return proxy
        return None

    def mark_failure(self, proxy_url: Optional[str]) -> None:
        proxy = self._find(proxy_url)
        if not proxy:
            return
        with self._lock:
            proxy["failures"] += 1
            proxy["cool_until"] = time.time() + self.cooldown_seconds
            if proxy["failures"] > self.max_failures:
                # If a proxy keeps failing, keep it on ice longer.
                proxy["cool_until"] += self.cooldown_seconds

    def mark_success(self, proxy_url: Optional[str]) -> None:
        proxy = self._find(proxy_url)
        if not proxy:
            return
        with self._lock:
            proxy["failures"] = 0
            proxy["cool_until"] = 0.0


def _build_pool() -> ProxyPool:
    proxies = getattr(settings, "PROXY_POOL", [])
    cooldown = getattr(settings, "PROXY_COOLDOWN_SECONDS", 60)
    max_failures = getattr(settings, "PROXY_MAX_FAILURES", 3)
    retry_statuses = getattr(settings, "PROXY_RETRY_STATUSES", {403, 429, 503})
    return ProxyPool(
        proxies=proxies,
        cooldown_seconds=cooldown,
        max_failures=max_failures,
        retry_statuses=retry_statuses,
    )


_GLOBAL_POOL = _build_pool()


def proxy_request(
    method: str,
    url: str,
    *,
    session: Optional[requests.Session] = None,
    max_attempts: Optional[int] = None,
    retry_statuses: Optional[Iterable[int]] = None,
    **kwargs,
) -> requests.Response:
    """
    Perform an HTTP request using the proxy pool with simple rotation and retry.
    - Falls back to direct connection if no proxies are configured or available.
    - Retries on network errors and on retry_statuses (e.g., 403/429/503).
    """
    pool = _GLOBAL_POOL
    statuses = set(retry_statuses or pool.retry_statuses)
    if max_attempts is None:
        max_attempts = max(len(pool), 0) + 1  # always allow a direct attempt

    requester = session.request if session else requests.request
    last_response: Optional[requests.Response] = None
    last_exception: Optional[Exception] = None

    for _ in range(max_attempts):
        proxy_url = pool.next_proxy() if pool else None
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        try:
            response = requester(method, url, proxies=proxies, **kwargs)
            last_response = response
            if statuses and response.status_code in statuses:
                pool.mark_failure(proxy_url)
                continue
            pool.mark_success(proxy_url)
            return response
        except requests.RequestException as exc:
            last_exception = exc
            pool.mark_failure(proxy_url)
            continue

    if last_response is not None:
        return last_response
    if last_exception:
        raise last_exception
    raise RuntimeError("proxy_request exhausted without a response.")


def add_proxy_to_chrome_options(options) -> Optional[str]:
    """
    If a proxy is available, attach it to the given ChromeOptions instance and
    return the proxy URL so callers can mark success/failure.
    """
    proxy_url = _GLOBAL_POOL.next_proxy()
    if proxy_url:
        options.add_argument(f"--proxy-server={proxy_url}")
    return proxy_url


def mark_proxy_failure(proxy_url: Optional[str]) -> None:
    _GLOBAL_POOL.mark_failure(proxy_url)


def mark_proxy_success(proxy_url: Optional[str]) -> None:
    _GLOBAL_POOL.mark_success(proxy_url)
