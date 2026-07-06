from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import UserModel
    from app.models.thend import ThendModel

class CommentModel(Base):
    __tablename__ = 'comment'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    thend_id: Mapped[int] = mapped_column(ForeignKey("thend.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    thend: Mapped["ThendModel"] = relationship("ThendModel", back_populates="comments")
    author: Mapped["UserModel"] = relationship("UserModel", back_populates="comments")