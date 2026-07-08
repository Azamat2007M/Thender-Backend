from pydantic import BaseModel
from datetime import datetime
from typing import List

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: int
    user_one_id: int
    user_two_id: int
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatCreateRequest(BaseModel):
    recipient_id: int