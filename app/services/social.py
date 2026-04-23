from __future__ import annotations

from cache.memory import TTLCache
from utils.keys import cache_key
from database import Database


class SocialService:
    def __init__(self, db: Database, cache: TTLCache | None = None):
        self.db = db
        self.cache = cache

    def follow(self, follower_id: int, following_id: int) -> bool:
        ok = self.db.follow_user(follower_id, following_id)
        if ok and self.cache:
            self.cache.delete(cache_key("profile", follower_id))
            self.cache.delete(cache_key("profile", following_id))
        return ok

    def unfollow(self, follower_id: int, following_id: int) -> bool:
        ok = self.db.unfollow_user(follower_id, following_id)
        if ok and self.cache:
            self.cache.delete(cache_key("profile", follower_id))
            self.cache.delete(cache_key("profile", following_id))
        return ok

    def get_profile(self, user_id: int) -> dict | None:
        if not self.cache:
            return self.db.get_public_profile(user_id)
        return self.cache.get_or_set(
            cache_key("profile", user_id),
            lambda: self.db.get_public_profile(user_id),
            ttl=60,
        )

    def get_feed(self, user_id: int, limit: int = 30) -> list:
        return self.db.get_activity_feed(user_id, limit=limit)

    def log_started_anime(self, user_id: int, anime_id: int):
        self.db.log_activity(user_id, "started_anime", anime_id=anime_id)

    def log_finished_episode(self, user_id: int, anime_id: int, episode_number: int):
        self.db.log_activity(user_id, "finished_episode", anime_id=anime_id, episode_number=episode_number)

    def get_active_viewers(self, anime_id: int, minutes: int = 10) -> int:
        return self.db.get_active_viewers(anime_id, minutes=minutes)

    def ping_watching(self, user_id: int, anime_id: int):
        self.db.ping_watch_session(user_id, anime_id)

