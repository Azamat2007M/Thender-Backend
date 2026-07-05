from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import auth
from app.database import get_db
from app.schemas.auth_schema import LoginRequest
from app.schemas.user_schema import UserResponse, UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def registration_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth.register_user(db, user_in)

@router.post("/login", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def login_user(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth.authenticate_user(db, login_data.email, login_data.password)
    return user
