from __future__ import annotations

from database import Database


class CommentsService:
    def __init__(self, db: Database):
        self.db = db

    def add_comment(self, anime_id: int, user_id: int, text: str, parent_id: int | None = None) -> int:
        return self.db.add_comment(anime_id, user_id, text, parent_id=parent_id)

    def like_comment(self, user_id: int, comment_id: int) -> bool:
        return self.db.like_comment(user_id, comment_id)

    def get_comments(self, anime_id: int, limit: int = 50) -> list:
        return self.db.get_comments(anime_id, limit=limit)

