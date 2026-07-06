from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.thend import ThendModel
    from app.models.comment import CommentModel


class UserModel(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    thends: Mapped[List["ThendModel"]] = relationship(
        "ThendModel",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["CommentModel"]] = relationship(
        "CommentModel",
        back_populates="author",
        cascade="all, delete-orphan"
    )