from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    """
    Ultra-light in-memory TTL cache.
    For 1M users, you'd switch to Redis, but this keeps architecture unchanged.
    """

    def __init__(self, default_ttl: int = 60):
        self._data: dict[str, _Entry] = {}
        self._default_ttl = int(default_ttl)

    def _now(self) -> float:
        return time.time()

    def get(self, key: str) -> Any:
        e = self._data.get(key)
        if not e:
            return None
        if e.expires_at <= self._now():
            self._data.pop(key, None)
            return None
        return e.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        t = self._default_ttl if ttl is None else int(ttl)
        self._data[key] = _Entry(value=value, expires_at=self._now() + max(t, 1))

    def get_or_set(self, key: str, fn: Callable[[], Any], ttl: int | None = None) -> Any:
        v = self.get(key)
        if v is not None:
            return v
        v = fn()
        self.set(key, v, ttl=ttl)
        return v

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def cleanup(self, max_scan: int = 5000) -> int:
        """
        Opportunistic cleanup to avoid unbounded growth.
        Returns number of removed keys.
        """
        now = self._now()
        removed = 0
        for i, (k, e) in enumerate(list(self._data.items())):
            if i >= max_scan:
                break
            if e.expires_at <= now:
                self._data.pop(k, None)
                removed += 1
        return removed

