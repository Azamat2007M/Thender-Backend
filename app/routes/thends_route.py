import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.config import settings
from app.models.user import UserModel
from app.schemas.thend_schema import ThendCreate, ThendResponse
from app.crud import thend as thend_crud
from app.crud.user import get_user_by_email

router = APIRouter(
    prefix="/thends",
    tags=["Thends (Posts)"]
)

async def get_current_user(
        access_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing from cookies. Please log in."
        )

    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    user = await get_user_by_email(db, email=email)

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user

@router.post("/", response_model=ThendResponse, status_code=status.HTTP_201_CREATED)
async def create_new_thend(
        payload: ThendCreate,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    return await thend_crud.create_thend(db=db, thend_data=payload, author_id=current_user.id)

@router.get("/", response_model=List[ThendResponse])
async def read_global_thends_feed(
        skip: int = 0,
        limit: int = 20,
        db: AsyncSession = Depends(get_db)
):
    return await thend_crud.get_all_thends(db=db, skip=skip, limit=limit)