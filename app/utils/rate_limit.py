from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    updated_at: float


class TokenBucketRateLimiter:
    """
    In-memory token bucket.
    For multi-instance scaling, replace storage with Redis (same interface).
    """

    def __init__(self, rate_per_sec: float, burst: int):
        self.rate = float(rate_per_sec)
        self.capacity = float(burst)
        self._buckets: dict[str, Bucket] = {}

    def allow(self, key: str, cost: float = 1.0) -> bool:
        now = time.time()
        b = self._buckets.get(key)
        if not b:
            self._buckets[key] = Bucket(tokens=self.capacity - cost, updated_at=now)
            return True

        # refill
        elapsed = max(0.0, now - b.updated_at)
        b.tokens = min(self.capacity, b.tokens + elapsed * self.rate)
        b.updated_at = now

        if b.tokens >= cost:
            b.tokens -= cost
            return True
        return False

    def cleanup(self, max_scan: int = 10000, ttl_sec: int = 3600) -> int:
        now = time.time()
        removed = 0
        for i, (k, b) in enumerate(list(self._buckets.items())):
            if i >= max_scan:
                break
            if now - b.updated_at > ttl_sec:
                self._buckets.pop(k, None)
                removed += 1
        return removed

