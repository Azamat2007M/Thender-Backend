from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import UserModel

class ChatModel(Base):
    __tablename__ = 'chat'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    user_one_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    user_two_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel", back_populates="chat", cascade="all, delete-orphan", order_by="MessageModel.created_at.asc()"
    )
    user_one: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[user_one_id])
    user_two: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[user_two_id])


class MessageModel(Base):
    __tablename__ = 'message'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    chat: Mapped["ChatModel"] = relationship("ChatModel", back_populates="messages")
    sender: Mapped["UserModel"] = relationship("UserModel")