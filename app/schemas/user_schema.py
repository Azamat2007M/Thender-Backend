from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.thend_schema import ThendResponse

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=4,
        max_length=16,
        description="The username must be between 4 and 16 characters long!"
    )
    email: EmailStr = Field(..., description="The email address must be provided!")
    password: str = Field(..., min_length=8, description="The password must be more than 8 characters long!")
    captcha_token: str = Field(..., description="The CAPTCHA token must be provided!")

class UserRegisterResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

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
    thends: List[ThendResponse] = []

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=4, max_length=16)
    email: Optional[None] = None 
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None