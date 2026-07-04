from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True
        # orm_mode = True

class UserUpdate(UserResponse):
    username: Optional[str] = None
    email: Optional[EmailStr] = None