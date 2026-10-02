"""
Telegram Mini App autentifikatsiyasi.

Bu fayl ikkita narsani qiladi:

1) Telegram WebApp yuborgan "initData" ni TEKSHIRADI - bu Telegram tomonidan
   botning tokeni bilan raqamli imzolangan ma'lumot. Agar imzo mos kelmasa,
   bu ma'lumot soxta (yoki boshqa botga tegishli) hisoblanadi va rad etiladi.
   Aynan shu tekshiruv soyasida foydalanuvchi o'zini boshqa birov qilib
   ko'rsata olmaydi (loyihaning 31-bandi: "Fake user ID bilan kirishga
   yo'l qo'yilmasin").

2) Tekshiruvdan o'tgan foydalanuvchi uchun ODDIY, o'zimiz imzolaydigan
   SESSIYA TOKENI yaratadi (JWT emas - qo'shimcha kutubxona kerak
   bo'lmasligi uchun ataylab shu yo'l tanlandi, lekin xavfsizlik printsipi
   bir xil: HMAC bilan imzolangan, muddati bor). Frontend shu tokenni
   keyingi so'rovlarda "Authorization: Bearer <token>" sifatida yuboradi.

Rasmiy Telegram algoritmi:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl

INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60  # 24 soat
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 kun


class AuthError(Exception):
    """initData yoki sessiya tokeni yaroqsiz bo'lganda ko'tariladi."""


def validate_init_data(init_data: str, bot_token: str) -> dict:
    """
    Telegram WebApp initData ni tekshiradi va ichidagi "user" JSON
    obyektini (dict) qaytaradi. Yaroqsiz bo'lsa AuthError ko'taradi.
    """
    if not init_data or not init_data.strip():
        raise AuthError("initData bo'sh")

    if not bot_token:
        raise AuthError("Server tomonda BOT_TOKEN sozlanmagan")

    pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise AuthError("initData ichida 'hash' yo'q")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise AuthError("initData imzosi mos kelmadi (soxta yoki o'zgartirilgan bo'lishi mumkin)")

    auth_date_raw = data.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        raise AuthError("initData ichida 'auth_date' yo'q yoki noto'g'ri")

    age = time.time() - int(auth_date_raw)
    if age > INIT_DATA_MAX_AGE_SECONDS:
        raise AuthError("initData muddati o'tgan, Mini App'ni qayta oching")
    if age < -300:  # kelajakdagi vaqt - soat sozlamasi noto'g'ri yoki soxtalashtirish
        raise AuthError("initData vaqti noto'g'ri")

    user_raw = data.get("user")
    if not user_raw:
        raise AuthError("initData ichida foydalanuvchi ma'lumoti yo'q")

    try:
        user = json.loads(user_raw)
    except (ValueError, TypeError) as exc:
        raise AuthError("Foydalanuvchi ma'lumotini o'qib bo'lmadi") from exc

    if not isinstance(user, dict) or not user.get("id"):
        raise AuthError("Foydalanuvchi ID topilmadi")

    return user


def create_session_token(telegram_id: int, session_secret: str) -> str:
    """Berilgan telegram_id uchun imzolangan, muddati bor sessiya tokeni yaratadi."""
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{telegram_id}:{expires_at}"
    signature = hmac.new(
        session_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    raw_token = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("ascii")


def verify_session_token(token: str, session_secret: str) -> int:
    """
    Sessiya tokenini tekshiradi va ichidagi telegram_id ni qaytaradi.
    Yaroqsiz/muddati o'tgan bo'lsa AuthError ko'taradi.
    """
    if not token:
        raise AuthError("Sessiya tokeni berilmagan")

    try:
        raw_token = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        telegram_id_str, expires_at_str, signature = raw_token.split(":")
    except Exception as exc:
        raise AuthError("Sessiya tokeni formati noto'g'ri") from exc

    payload = f"{telegram_id_str}:{expires_at_str}"
    expected_signature = hmac.new(
        session_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise AuthError("Sessiya tokeni imzosi noto'g'ri")

    if not expires_at_str.isdigit() or int(expires_at_str) < time.time():
        raise AuthError("Sessiya muddati tugagan, qayta kiring")

    if not telegram_id_str.lstrip("-").isdigit():
        raise AuthError("Sessiya tokeni ichidagi ID noto'g'ri")

    return int(telegram_id_str)
