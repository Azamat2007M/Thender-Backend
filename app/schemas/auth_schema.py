from pydantic import BaseModel, EmailStr
from app.schemas.user_schema import UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    user_id: int | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str