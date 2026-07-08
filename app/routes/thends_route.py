import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.config import settings
from app.models.user import UserModel
from app.models.thend import ThendModel
from app.schemas.thend_schema import ThendCreate, ThendResponse, ThendDetailResponse
from app.crud import thend as thend_crud
from app.crud.user import get_user_by_email
from app.schemas.comment_schema import CommentCreate, CommentResponse

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


async def get_optional_current_user(
        access_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db)
) -> UserModel | None:
    if not access_token:
        return None
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = await get_user_by_email(db, email=email)
        return user if user and user.is_active else None
    except jwt.PyJWTError:
        return None


@router.post("/", response_model=ThendResponse, status_code=status.HTTP_201_CREATED)
async def create_new_thend(
        payload: ThendCreate,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    thend_obj = await thend_crud.create_thend(db=db, thend_data=payload, author_id=current_user.id)
    thend_obj.is_liked = False
    thend_obj.likes_count = 0
    return thend_obj


@router.get("/", response_model=List[ThendResponse])
async def read_global_thends_feed(
        skip: int = 0,
        limit: int = 20,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel | None = Depends(get_optional_current_user)
):
    stmt = (
        select(ThendModel)
        .options(
            selectinload(ThendModel.author),
            selectinload(ThendModel.liked_by_users),
            selectinload(ThendModel.comments)
        )
        .order_by(ThendModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    thends = result.scalars().all()

    for thend in thends:
        thend.likes_count = len(thend.liked_by_users)
        thend.is_liked = any(user.id == current_user.id for user in thend.liked_by_users) if current_user else False

        thend.comments_count = len(thend.comments)

    return thends


@router.post("/{thend_id}/like", response_model=ThendResponse)
async def toggle_thend_like(
        thend_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    updated_thend = await thend_crud.toggle_like_thend(db=db, thend_id=thend_id, user_id=current_user.id)
    if not updated_thend:
        raise HTTPException(status_code=404, detail="Thend not found")

    db.expire(updated_thend)

    stmt = (
        select(ThendModel)
        .options(selectinload(ThendModel.author), selectinload(ThendModel.liked_by_users))
        .where(ThendModel.id == thend_id)
    )
    res = await db.execute(stmt)
    thend_obj = res.scalar_one()

    thend_obj.is_liked = any(user.id == current_user.id for user in thend_obj.liked_by_users)
    thend_obj.likes_count = len(thend_obj.liked_by_users)

    return thend_obj

@router.get("/me", response_model=List[ThendResponse])
async def read_my_thends(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    stmt = (
        select(ThendModel)
        .options(
            selectinload(ThendModel.author),
            selectinload(ThendModel.liked_by_users),
            selectinload(ThendModel.comments)
        )
        .where(ThendModel.author_id == current_user.id)
        .order_by(ThendModel.created_at.desc())
    )
    result = await db.execute(stmt)
    thends = result.scalars().all()

    for thend in thends:
        thend.likes_count = len(thend.liked_by_users)
        thend.is_liked = any(user.id == current_user.id for user in thend.liked_by_users)
        thend.comments_count = len(thend.comments)

    return thends

@router.get("/liked", response_model=List[ThendResponse])
async def read_my_liked_thends(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    stmt = (
        select(ThendModel)
        .join(ThendModel.liked_by_users)
        .options(
            selectinload(ThendModel.author),
            selectinload(ThendModel.liked_by_users),
            selectinload(ThendModel.comments)
        )
        .where(UserModel.id == current_user.id)
        .order_by(ThendModel.created_at.desc())
    )
    result = await db.execute(stmt)
    thends = result.scalars().all()

    for thend in thends:
        thend.likes_count = len(thend.liked_by_users)
        thend.is_liked = True
        thend.comments_count = len(thend.comments)

    return thends


@router.get("/{thend_id}", response_model=ThendDetailResponse)
async def read_single_thend(
        thend_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel | None = Depends(get_optional_current_user)
):
    thend = await thend_crud.get_thend_by_id(db, thend_id)
    if not thend:
        raise HTTPException(status_code=404, detail="Thend not found")

    thend.likes_count = len(thend.liked_by_users)
    thend.is_liked = any(user.id == current_user.id for user in thend.liked_by_users) if current_user else False

    thend.comments_count = len(thend.comments)

    return thend

@router.post("/{thend_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_thend_comment(
        thend_id: int,
        payload: CommentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    thend = await thend_crud.get_thend_by_id(db, thend_id)
    if not thend:
        raise HTTPException(status_code=404, detail="Thend not found")

    return await thend_crud.create_comment(
        db=db,
        comment_data=payload,
        thend_id=thend_id,
        author_id=current_user.id
    )

