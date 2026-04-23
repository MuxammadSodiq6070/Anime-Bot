from __future__ import annotations

from cache.memory import TTLCache
from utils.keys import cache_key
from database import Database


class RecommendationService:
    def __init__(self, db: Database, cache: TTLCache | None = None):
        self.db = db
        self.cache = cache

    def get_recommended_anime(self, user_id: int, limit: int = 10) -> list:
        if not self.cache:
            return self.db.get_recommended_anime(user_id, limit=limit)
        # cache short-lived: feed can change quickly
        return self.cache.get_or_set(
            cache_key("recs", user_id, limit),
            lambda: self.db.get_recommended_anime(user_id, limit=limit),
            ttl=30,
        )

