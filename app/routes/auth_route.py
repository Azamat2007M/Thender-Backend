import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import get_user_by_email
from app.database import get_db
from app.models.user import UserModel
from app.schemas.auth_schema import LoginRequest, Token, GoogleAuthRequest
from app.schemas.user_schema import UserCreate, UserRegisterResponse
from app.crud import auth
from app.core.security import create_access_token, hash_password, verify_turnstile
from app.config import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def registration_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    await verify_turnstile(user_in.captcha_token)
    return await auth.register_user(db, user_in)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    await verify_turnstile(login_data.captcha_token)
    user = await auth.authenticate_user(db, login_data.email, login_data.password)
    access_token = create_access_token(data={"sub": user.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 24 * 60
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", status_code=status.HTTP_200_OK)
async def google_auth(
    auth_data: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    try:
        id_info = id_token.verify_oauth2_token(
            auth_data.token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID 
        )
        
        email = id_info.get("email")
        username = id_info.get("name")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google account")
            
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    user = await get_user_by_email(db, email)

    if not user:
        random_password = hash_password(secrets.token_hex(16))
        clean_username = username.replace(" ", "_").lower()[:16]
        
        user = UserModel(
            username=clean_username,
            email=email,
            password=random_password,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(data={"sub": user.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  
        samesite="none",
        max_age=60 * 24 * 60
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    }