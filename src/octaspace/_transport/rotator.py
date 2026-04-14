from __future__ import annotations

import threading
import time


class UrlRotator:
    def __init__(self, urls: list[str], *, failure_cooldown: float = 30.0) -> None:
        self._urls = list(urls)
        self._failure_cooldown = failure_cooldown
        self._failed: dict[str, float] = {}
        self._counter = 0
        self._lock = threading.Lock()

    @property
    def failure_cooldown(self) -> float:
        return self._failure_cooldown

    def next_url(self) -> str:
        with self._lock:
            available = self._available_urls_locked(time.monotonic())
            if not available:
                return self._urls[0]
            index = self._counter % len(available)
            self._counter += 1
            return available[index]

    def mark_failed(self, url: str) -> None:
        with self._lock:
            self._failed[url] = time.monotonic()

    def mark_success(self, url: str) -> None:
        with self._lock:
            self._failed.pop(url, None)

    def available_urls(self) -> list[str]:
        with self._lock:
            return self._available_urls_locked(time.monotonic())

    def stats(self) -> dict[str, object]:
        with self._lock:
            available = self._available_urls_locked(time.monotonic())
            return {
                "total": len(self._urls),
                "available": len(available),
                "failed": list(self._failed.keys()),
                "failure_cooldown": self._failure_cooldown,
            }

    def reset(self) -> None:
        with self._lock:
            self._counter = 0
            self._failed.clear()

    def _available_urls_locked(self, now: float) -> list[str]:
        available: list[str] = []
        expired: list[str] = []
        for url in self._urls:
            failed_at = self._failed.get(url)
            if failed_at is None:
                available.append(url)
                continue
            if now - failed_at >= self._failure_cooldown:
                expired.append(url)
                available.append(url)
        for url in expired:
            self._failed.pop(url, None)
        return available
