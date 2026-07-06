from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from app.schemas.comment_schema import CommentResponse


class ThendBase(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Text of the content",
        examples=["Created project using FastApi + Docker"]
    )


class ThendCreate(ThendBase):
    pass


class ThendAuthorResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True


# Базовый ответ для ленты, создания и лайков
class ThendResponse(ThendBase):
    id: int
    likes_count: int
    views_count: int
    created_at: datetime
    author_id: int
    is_liked: bool = False
    author: ThendAuthorResponse

    # ДОБАВИЛИ ПОЛЕ ДЛЯ СЧЕТЧИКА:
    comments_count: int = 0

    class Config:
        from_attributes = True


# Детальный ответ (для страницы отдельного поста)
class ThendDetailResponse(ThendResponse):
    comments: List[CommentResponse] = []