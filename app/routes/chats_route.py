from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
import json

from app.database import get_db
from app.models.chat import ChatModel, MessageModel
from app.models.user import UserModel
from app.schemas.chat_schema import ChatResponse, ChatCreateRequest
from app.routes.thends_route import get_current_user  
from app.core.chat_manager import manager

router = APIRouter(
    prefix="/chats",
    tags=["Chats"],
)


@router.post("/get-or-create", response_model=ChatResponse)
async def get_or_create_chat(
        body: ChatCreateRequest,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    if current_user.id == body.recipient_id:
        raise HTTPException(status_code=400, detail="Нельзя создать чат с самим собой")

    stmt = select(ChatModel).options(selectinload(ChatModel.messages)).where(
        or_(
            and_(ChatModel.user_one_id == current_user.id, ChatModel.user_two_id == body.recipient_id),
            and_(ChatModel.user_one_id == body.recipient_id, ChatModel.user_two_id == current_user.id)
        )
    )
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if not chat:
        chat = ChatModel(user_one_id=current_user.id, user_two_id=body.recipient_id)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        chat.messages = []  

    return chat

@router.get("/my-chats", response_model=list[ChatResponse])
async def get_my_chats(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    stmt = (
        select(ChatModel)
        .options(selectinload(ChatModel.messages))
        .where(
            or_(
                ChatModel.user_one_id == current_user.id,
                ChatModel.user_two_id == current_user.id
            )
        )
    )
    result = await db.execute(stmt)
    chats = result.scalars().all()
    return chats


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        await websocket.close(code=1003)
        return

    await manager.connect(chat_id_int, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_json = json.loads(data)

            sender_id = message_json.get("sender_id")
            text = message_json.get("text")

            if not text or not sender_id:
                continue

            async for db in get_db():
                new_message = MessageModel(chat_id=chat_id_int, sender_id=int(sender_id), text=text)
                db.add(new_message)
                await db.commit()
                await db.refresh(new_message)

                broadcast_data = {
                    "id": new_message.id,
                    "chat_id": chat_id_int,
                    "sender_id": int(sender_id),
                    "text": text,
                    "created_at": new_message.created_at.isoformat()
                }
                
                await manager.broadcast_to_chat(chat_id_int, broadcast_data)
                break 

    except WebSocketDisconnect:
        manager.disconnect(chat_id_int, websocket)
    except Exception as e:
        print(f"Внутренняя ошибка в WS: {e}")
        manager.disconnect(chat_id_int, websocket)