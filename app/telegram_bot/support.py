from fastapi import APIRouter, HTTPException, status
from app.schemas.support_scheme import SupportRequest
from app.config import settings
import httpx

router = APIRouter(
    prefix="/support",
    tags=["Support & Feedback"]
)

TELEGRAM_TOKEN = settings.TELEGRAM_BOT_TOKEN
ADMIN_CHAT_ID = settings.TELEGRAM_ADMIN_CHAT_ID

@router.post("/report")
async def send_report_to_telegram(payload: SupportRequest):
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot configuration is missing on the server."
        )

    tg_message = (
        f"🚨 <b>Новый фидбек на Thender!</b>\n\n"
        f"👤 <b>Отправитель:</b> @{payload.username}\n"
        f"📌 <b>Тип:</b> {payload.message_type}\n\n"
        f"📝 <b>Описание:</b>\n{payload.description}"
    )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                telegram_url,
                json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": tg_message,
                    "parse_mode": "HTML"
                },
                timeout=10.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Telegram API error: {response.text}"
                )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to Telegram servers: {exc}"
            )

    return {"status": "success", "message": "Report successfully routed to Telegram Admin."}