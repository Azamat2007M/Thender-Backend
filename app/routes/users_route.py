from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user_schema import UserResponse, UserCreate, UserUpdate
from app.models.user import UserModel
from app.models.thend import thend_likes
from app.models.comment import CommentModel
from app.crud import user as crud_user
from app.routes.thends_route import get_current_user
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from typing import List, Optional

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users_data = await crud_user.get_users(db)
    return users_data


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    stmt = (
        select(UserModel)
        .options(
            selectinload(UserModel.followers),
            selectinload(UserModel.following),
            selectinload(UserModel.thends)
        )
        .where(UserModel.id == current_user.id)
    )
    result = await db.execute(stmt)
    user_with_relations = result.scalar_one()

    user_with_relations.followers_count = len(user_with_relations.followers)
    user_with_relations.following_count = len(user_with_relations.following)

    if user_with_relations.thends:
        for t in user_with_relations.thends:
            likes_stmt = select(func.count()).where(thend_likes.c.thend_id == t.id)
            likes_res = await db.execute(likes_stmt)
            t.likes_count = likes_res.scalar()

            comments_stmt = select(func.count()).where(CommentModel.thend_id == t.id)
            comments_res = await db.execute(comments_stmt)
            t.comments_count = comments_res.scalar()

            my_like_stmt = select(func.count()).where(
                thend_likes.c.thend_id == t.id,
                thend_likes.c.user_id == current_user.id
            )
            my_like_res = await db.execute(my_like_stmt)
            t.is_liked = my_like_res.scalar() > 0  

    return user_with_relations


@router.get("/by-username/{username}", response_model=UserResponse)
async def get_user_profile_with_posts(
        username: str,
        db: AsyncSession = Depends(get_db),
        current_user: Optional[UserModel] = Depends(get_current_user)
):
    stmt = (
        select(UserModel)
        .options(
            selectinload(UserModel.thends),
            selectinload(UserModel.followers),
            selectinload(UserModel.following)
        )
        .where(UserModel.username == username)
    )

    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    db_user.followers_count = len(db_user.followers)
    db_user.following_count = len(db_user.following)

    db_user.is_following = False
    if current_user and current_user.id != db_user.id:
        db_user.is_following = any(f.id == current_user.id for f in db_user.followers)

    if db_user.thends:
        for t in db_user.thends:
            likes_query = select(func.count()).where(thend_likes.c.thend_id == t.id)
            likes_result = await db.execute(likes_query)
            t.likes_count = likes_result.scalar()

            comments_query = select(func.count()).where(CommentModel.thend_id == t.id)
            comments_result = await db.execute(comments_query)
            t.comments_count = comments_result.scalar()

            if current_user:
                is_liked_query = select(func.count()).where(
                    thend_likes.c.thend_id == t.id,
                    thend_likes.c.user_id == current_user.id
                )
                is_liked_result = await db.execute(is_liked_query)
                t.is_liked = is_liked_result.scalar() > 0  
            else:
                t.is_liked = False

    return db_user


@router.post("/{user_id}/follow", status_code=status.HTTP_200_OK)
async def follow_unfollow_user(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Вы не можете подписаться на самого себя")

    stmt = select(UserModel).options(selectinload(UserModel.followers)).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    stmt_me = select(UserModel).options(selectinload(UserModel.following)).where(UserModel.id == current_user.id)
    res_me = await db.execute(stmt_me)
    me = res_me.scalar_one()

    if target_user in me.following:
        me.following.remove(target_user)
        message = "Успешная отписка"
    else:
        me.following.append(target_user)
        message = "Успешная подписка"

    await db.commit()
    return {"detail": message}


@router.get("/{user_id}", response_model=UserResponse)
async def get_users(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user) 
):
    stmt = (
        select(UserModel)
        .options(
            selectinload(UserModel.followers),
            selectinload(UserModel.following),
            selectinload(UserModel.thends)
        )
        .where(UserModel.id == user_id)
    )
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    db_user.followers_count = len(db_user.followers)
    db_user.following_count = len(db_user.following)
    
    db_user.is_following = False
    if current_user and current_user.id != db_user.id:
        db_user.is_following = any(f.id == current_user.id for f in db_user.followers)
        
    if db_user.thends:
        for t in db_user.thends:
            t.likes_count = 0
            t.comments_count = 0
            t.is_liked = False

    return db_user


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    if await crud_user.get_user_by_email(db, user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")
    if await crud_user.get_user_by_username(db, user.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    return await crud_user.create_user(db, user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update_body: UserUpdate, db: AsyncSession = Depends(get_db)):
    user_data = await crud_user.get_user_by_id(db, user_id)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update_body.email and user_update_body.email != user_data.email:
        if await crud_user.get_user_by_email(db, user_update_body.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")

    if user_update_body.username and user_update_body.username != user_data.username:
        if await crud_user.get_user_by_username(db, user_update_body.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    return await crud_user.update_user(db, user_data, user_update_body)


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_data = await crud_user.get_user_by_id(db, user_id)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await crud_user.delete_user(db, user_data)