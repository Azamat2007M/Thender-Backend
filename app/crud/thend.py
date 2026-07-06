from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.comment import CommentModel
from app.models.thend import ThendModel, thend_likes
from app.schemas.thend_schema import ThendCreate
from sqlalchemy import insert, delete, and_
from app.schemas.comment_schema import CommentCreate


async def create_thend(db: AsyncSession, thend_data: ThendCreate, author_id: int) -> ThendModel:
    # 1. Создаем объект поста
    new_thend = ThendModel(
        content=thend_data.content,
        author_id=author_id
    )
    db.add(new_thend)

    # 2. Фиксируем в базе данных, чтобы сгенерировался id и created_at
    await db.commit()

    # 3. Делаем чистый, изолированный запрос свежего поста сразу с автором
    stmt = (
        select(ThendModel)
        .options(selectinload(ThendModel.author))
        .where(ThendModel.id == new_thend.id)
    )
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
        .options(selectinload(ThendModel.author), selectinload(ThendModel.liked_by_users), selectinload(ThendModel.comments).selectinload(CommentModel.author))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def toggle_like_thend(db: AsyncSession, thend_id: int, user_id: int) -> ThendModel | None:
    thend = await get_thend_by_id(db, thend_id)
    if not thend:
        return None

    stmt = select(thend_likes).where(
        and_(thend_likes.c.user_id == user_id, thend_likes.c.thend_id == thend_id)
    )
    result = await db.execute(stmt)
    like_exists = result.first()

    if like_exists:
        delete_stmt = delete(thend_likes).where(
            and_(thend_likes.c.user_id == user_id, thend_likes.c.thend_id == thend_id)
        )
        await db.execute(delete_stmt)
        thend.likes_count = max(0, thend.likes_count - 1)  # Чтобы счетчик не ушел в минус
    else:
        insert_stmt = insert(thend_likes).values(user_id=user_id, thend_id=thend_id)
        await db.execute(insert_stmt)
        thend.likes_count += 1

    await db.commit()

    stmt_refresh = select(ThendModel).where(ThendModel.id == thend_id).options(selectinload(ThendModel.author))
    res_refresh = await db.execute(stmt_refresh)
    return res_refresh.scalar_one()


async def create_comment(db: AsyncSession, comment_data: CommentCreate, thend_id: int, author_id: int) -> CommentModel:
    new_comment = CommentModel(
        content=comment_data.content,
        thend_id=thend_id,
        author_id=author_id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    stmt = select(CommentModel).where(CommentModel.id == new_comment.id).options(selectinload(CommentModel.author))
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_thend(db: AsyncSession, thend_id: int, author_id: int) -> bool:
    thend = await get_thend_by_id(db, thend_id)
    if not thend or thend.author_id != author_id:
        return False

    await db.delete(thend)
    await db.commit()
    return True
