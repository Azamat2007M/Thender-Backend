from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

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

    return new_user

async def authenticate_user(db: AsyncSession, email: str, password_to_check: str):
    user_data = await crud_user.get_user_by_email(db, email)

    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not available")

    if not verify_password(password_to_check, user_data.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    if not user_data.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user_data