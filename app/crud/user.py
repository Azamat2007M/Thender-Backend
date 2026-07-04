from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.schemes.user_scheme import UserCreate, UserUpdate


async def get_users(db: AsyncSession):
    query = select(UserModel)

    result = await db.execute(query)

    return result.scalars().all()

async def get_user_by_id(db: AsyncSession, user_id: int):
    query = select(UserModel).where(UserModel.id == user_id)

    result = await db.execute(query)

    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate):
    new_user = UserModel(
        username=user.username,
        email=user.email,
    )

    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return new_user

async def update_user(db: AsyncSession, user: UserModel, user_update: UserUpdate):
    data_to_update = user_update.model_dump(exclude_unset=True)

    for key, value in data_to_update.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user

async def delete_user(db: AsyncSession, user: UserModel):
    await db.delete(user)
    await db.commit()

    return user
