from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserThendResponse(BaseModel):
    id: int
    content: str
    likes_count: int = 0
    views_count: int = 0
    comments_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=4,
        max_length=16,
        description="The username must be between 4 and 16 characters long!"
    )
    email: EmailStr = Field(..., description="The email address must be provided!")
    password: str = Field(..., min_length=8, description="The password must be more than 8 characters long!")

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    followers_count: int | None = 0
    following_count: int | None = 0
    is_following: bool = False
    thends: List[UserThendResponse] = []

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=4, max_length=16)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None