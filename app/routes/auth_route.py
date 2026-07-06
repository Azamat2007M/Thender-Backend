from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth_schema import LoginRequest, Token
from app.schemas.user_schema import UserResponse, UserCreate
from app.crud import auth
from app.core.security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def registration_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth.register_user(db, user_in)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user = await auth.authenticate_user(db, login_data.email, login_data.password)
    access_token = create_access_token(data={"sub": user.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 24 * 60
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }