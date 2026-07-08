from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.user import UserModel
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password, verify_password
from app.crud import user as crud_user

async def register_user(db: AsyncSession, user_data: UserCreate):
    is_email_exist = await crud_user.get_user_by_email(db, user_data.email)
    is_username_exist = await crud_user.get_user_by_username(db, user_data.username)

    if is_email_exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    elif is_username_exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = hash_password(user_data.password)

    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    new_user.thends = []
    new_user.followers = []
    new_user.following = []
    new_user.followers_count = 0
    new_user.following_count = 0
    new_user.is_following = False

    return new_user

async def authenticate_user(db: AsyncSession, email: str, password_to_check: str):
    query = (
        select(UserModel)
        .options(
            selectinload(UserModel.thends),
            selectinload(UserModel.followers),
            selectinload(UserModel.following)
        )
        .where(UserModel.email == email)
    )
    result = await db.execute(query)
    user_data = result.scalar_one_or_none()

    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not available")

    if not verify_password(password_to_check, user_data.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    if not user_data.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    user_data.followers_count = len(user_data.followers)
    user_data.following_count = len(user_data.following)
    user_data.is_following = False


    if user_data.thends:
        for t in user_data.thends:
            t.likes_count = 0
            t.comments_count = 0

    return user_data