from sqlalchemy import ForeignKey, func, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import UserModel
    from app.models.comment import CommentModel

thend_likes = Table(
    "thend_like",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("thend_id", Integer, ForeignKey("thend.id", ondelete="CASCADE"), primary_key=True),
)


class ThendModel(Base):
    __tablename__ = 'thend'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(nullable=False)

    likes_count: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    views_count: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    author: Mapped["UserModel"] = relationship("UserModel", back_populates="thends")
    comments: Mapped[List["CommentModel"]] = relationship("CommentModel", back_populates="thend", cascade="all, delete-orphan")

    liked_by_users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        secondary=thend_likes,
        back_populates="liked_thends"
    )