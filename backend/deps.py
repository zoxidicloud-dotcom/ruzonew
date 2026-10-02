"""
FastAPI so'rovlarida joriy (autentifikatsiyadan o'tgan) foydalanuvchini
"Authorization: Bearer <token>" headeridan aniqlash uchun umumiy dependency.

Bu fayl auth.py dan ajratilgan, chunki auth.py atayin FastAPI'ga bog'liq
bo'lmagan sof Python bo'lib qoladi (shu tufayli uni sqlalchemy/fastapi
o'rnatilmagan muhitda ham alohida sinash mumkin edi).
"""

from typing import Optional

from fastapi import Header, HTTPException

from auth import AuthError, verify_session_token
from config import settings


def get_current_telegram_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Avtorizatsiya talab qilinadi")

    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_session_token(token, settings.SESSION_SECRET)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
