from __future__ import annotations

from cache.memory import TTLCache
from database import Database


class ShortsService:
    def __init__(self, db: Database, cache: TTLCache | None = None):
        self.db = db
        self.cache = cache

    def get_next(self, user_id: int) -> dict | None:
        return self.db.get_next_short(user_id)

    def register_view(self, short_id: int):
        self.db.increment_short_view(short_id)

    def like(self, user_id: int, short_id: int) -> bool:
        return self.db.like_short(user_id, short_id)

    def unlike(self, user_id: int, short_id: int) -> bool:
        return self.db.unlike_short(user_id, short_id)

    def track(self, user_id: int, short_id: int, watch_time: float = 0, skipped: int = 0, rewatched: int = 0):
        self.db.track_short_engagement(user_id, short_id, watch_time=watch_time, skipped=skipped, rewatched=rewatched)

