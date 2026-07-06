from pydantic import BaseModel, Field
from datetime import datetime

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
    likes_count: int
    views_count: int
    created_at: datetime
    author_id: int

    author: ThendAuthorResponse

    class Config:
        from_attributes = True