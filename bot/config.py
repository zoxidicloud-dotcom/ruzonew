"""
Bot uchun konfiguratsiya.

Bu fayl backend/config.py bilan bir xil ".env" faylini o'qiydi (loyihaning
ROOT papkasida), lekin faqat botga kerak bo'lgan qiymatlarni ochib beradi.
"""

import os

from dotenv import load_dotenv

# gaming_shop/bot/config.py -> gaming_shop/ (ROOT papka)
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


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_TELEGRAM_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_TELEGRAM_IDS", ""))
ADMIN_CHANNEL_ID: str = os.getenv("ADMIN_CHANNEL_ID", "").strip()

PAYMENT_CARD_NUMBER: str = os.getenv("PAYMENT_CARD_NUMBER", "").strip()
PAYMENT_CARD_NAME: str = os.getenv("PAYMENT_CARD_NAME", "").strip()

WEBSITE_URL: str = os.getenv("WEBSITE_URL", "").strip()
SHOP_NAME: str = os.getenv("SHOP_NAME", "Gaming Shop").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi!\n\n"
        "Iltimos, loyihaning ASOSIY (ROOT) papkasida '.env' faylini yarating:\n"
        "  1) '.env.example' faylidan nusxa oling va nomini '.env' ga o'zgartiring\n"
        "  2) BOT_TOKEN qatoriga @BotFather bergan tokenni kiriting\n"
    )
