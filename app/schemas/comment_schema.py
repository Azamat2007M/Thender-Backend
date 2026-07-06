from pydantic import BaseModel
from datetime import datetime

class CommentAuthorResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    thend_id: int
    author_id: int
    author: CommentAuthorResponse  # Используем локальную схему

    class Config:
        from_attributes = True