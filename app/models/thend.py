from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import UserModel
    from app.models.comment import CommentModel

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

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    author: Mapped["UserModel"] = relationship("UserModel", back_populates="thends")
    comments: Mapped[List["CommentModel"]] = relationship("CommentModel", back_populates="thend", cascade="all, delete-orphan")