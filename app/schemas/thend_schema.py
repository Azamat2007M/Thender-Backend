from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, List, Optional
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

class ThendResponse(ThendBase):
    id: int
    image_url: Optional[str] = None 
    likes_count: int
    views_count: int
    created_at: datetime
    author_id: int
    is_liked: bool = False
    author: ThendAuthorResponse
    comments_count: int = 0

    class Config:
        from_attributes = True

class ThendDetailResponse(ThendResponse):
    comments: List[CommentResponse] = []

class SearchResultResponse(BaseModel):
    posts: List[ThendResponse] 
    channels: List[Dict[str, Any]]