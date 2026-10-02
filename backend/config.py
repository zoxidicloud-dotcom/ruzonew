"""
Backend uchun konfiguratsiya.

Barcha maxfiy/o'zgaruvchan qiymatlar (token, ID, karta raqami) kodga
yozilmaydi - ular loyihaning ROOT papkasidagi ".env" faylidan o'qiladi.
"""

import os

from dotenv import load_dotenv

# gaming_shop/backend/config.py -> gaming_shop/  (ROOT papka)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)


def _parse_admin_ids(raw: str) -> list[int]:
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_TELEGRAM_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_TELEGRAM_IDS", ""))
    ADMIN_CHANNEL_ID: str = os.getenv("ADMIN_CHANNEL_ID", "")

    PAYMENT_CARD_NUMBER: str = os.getenv("PAYMENT_CARD_NUMBER", "")
    PAYMENT_CARD_NAME: str = os.getenv("PAYMENT_CARD_NAME", "")

    REFERRAL_REWARD: int = int(os.getenv("REFERRAL_REWARD", "1000"))
    SHOP_NAME: str = os.getenv("SHOP_NAME", "Gaming Shop")

    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "")


settings = Settings()

if not settings.SESSION_SECRET:
    raise RuntimeError(
        "SESSION_SECRET topilmadi!\n\n"
        "Bu Telegram Mini App sessiyalarini imzolash uchun ishlatiladigan "
        "maxfiy kalit. Iltimos, '.env' fayliga uzun, tasodifiy qator "
        "qo'shing, masalan:\n"
        "  SESSION_SECRET=juda-uzun-tasodifiy-va-maxfiy-qator-2026\n\n"
        "(.env.example fayliga qarang)"
    )
