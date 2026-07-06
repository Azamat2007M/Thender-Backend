from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.thend import ThendModel
from app.schemas.thend_schema import ThendCreate

async def create_thend(db: AsyncSession, thend_data: ThendCreate, author_id: int) -> ThendModel:
    new_thend = ThendModel(
        content=thend_data.content,
        author_id=author_id
    )
    db.add(new_thend)
    await db.commit()
    await db.refresh(new_thend)

    stmt = select(ThendModel).where(ThendModel.id == new_thend.id).options(selectinload(ThendModel.author))
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_all_thends(db: AsyncSession, skip: int = 0, limit: int = 20):
    stmt = (
        select(ThendModel)
        .options(selectinload(ThendModel.author))
        .order_by(ThendModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_thend_by_id(db: AsyncSession, thend_id: int) -> ThendModel | None:
    stmt = (
        select(ThendModel)
        .where(ThendModel.id == thend_id)
        .options(selectinload(ThendModel.author), selectinload(ThendModel.comments))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def toggle_like_thend(db: AsyncSession, thend_id: int) -> ThendModel | None:
    thend = await get_thend_by_id(db, thend_id)
    if thend:
        thend.likes_count += 1
        await db.commit()
        await db.refresh(thend)
    return thend


async def delete_thend(db: AsyncSession, thend_id: int, author_id: int) -> bool:
    thend = await get_thend_by_id(db, thend_id)
    if not thend or thend.author_id != author_id:
        return False

    await db.delete(thend)
    await db.commit()
    return True