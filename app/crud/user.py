from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.schemes.user_scheme import UserCreate

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