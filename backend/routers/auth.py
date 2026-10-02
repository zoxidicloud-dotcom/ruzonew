"""
Telegram Mini App autentifikatsiyasi.

Frontend Telegram ichida ochilganda, Telegram WebApp SDK bergan "initData"
ni shu endpointga yuboradi. Biz uni tekshiramiz (auth.py), foydalanuvchini
topamiz/yaratamiz va imzolangan sessiya tokenini qaytaramiz - frontend
keyingi so'rovlarda shu tokenni "Authorization: Bearer <token>" sifatida
yuboradi.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import AuthError, create_session_token, validate_init_data
from config import settings
from database import get_db
from services import user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TelegramAuthRequest(BaseModel):
    init_data: str


class TelegramAuthResponse(BaseModel):
    token: str


@router.post("/telegram", response_model=TelegramAuthResponse)
def telegram_auth(payload: TelegramAuthRequest, db: Session = Depends(get_db)):
    try:
        tg_user = validate_init_data(payload.init_data, settings.BOT_TOKEN)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    user = user_service.get_or_create_user(
        db,
        telegram_id=tg_user["id"],
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        last_name=tg_user.get("last_name"),
    )

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Hisobingiz bloklangan")

    token = create_session_token(user.telegram_id, settings.SESSION_SECRET)
    return TelegramAuthResponse(token=token)
