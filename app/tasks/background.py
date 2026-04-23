from __future__ import annotations

import asyncio

from cache.memory import TTLCache


async def cache_maintenance_loop(cache: TTLCache, interval_sec: int = 60):
    while True:
        try:
            cache.cleanup(max_scan=5000)
        except Exception:
            pass
        await asyncio.sleep(max(5, int(interval_sec)))

