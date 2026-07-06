from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import hash_password

async def get_users(db: AsyncSession):
    query = select(UserModel)
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_by_id(db: AsyncSession, user_id: int):
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    query = select(UserModel).where(UserModel.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str):
    query = select(UserModel).where(UserModel.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate):
    new_user = UserModel(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def update_user(db: AsyncSession, user: UserModel, user_update: UserUpdate):
    data_to_update = user_update.model_dump(exclude_unset=True)

    for key, value in data_to_update.items():
        if key == "password" and value:
            value = hash_password(value)
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user: UserModel):
    await db.delete(user)
    await db.commit()
    return user