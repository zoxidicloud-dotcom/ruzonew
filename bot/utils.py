"""Bot uchun kichik yordamchi funksiyalar."""

import html
import re
from datetime import timedelta
from typing import Optional

GENERIC_ERROR = "❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."


def format_price(amount: float) -> str:
    """12000 -> "12 000 so'm" """
    return f"{int(round(amount)):,}".replace(",", " ") + " so'm"


def esc(value) -> str:
    """
    Foydalanuvchi kiritgan matnni HTML'ga xavfsiz qiladi. Bot parse_mode="HTML"
    bilan ishlaydi, shuning uchun username/ism kabi tashqi matnlar albatta
    shu funksiyadan o'tkazilishi kerak (aks holda "<" belgisi xabarni buzadi).
    """
    if value is None:
        return ""
    return html.escape(str(value))


def is_cancel(message) -> bool:
    """
    Foydalanuvchi ko'p bosqichli jarayonni bekor qilmoqchimi (asosiy menyu
    tugmasini bosdimi yoki /buyruq yubordimi). balance.py va shop.py dagi
    barcha ko'p bosqichli jarayonlar shu funksiyadan foydalanadi.
    """
    from keyboards import MENU_BUTTONS  # aylanma import'dan qochish uchun shu yerda

    if message.content_type != "text":
        return False
    text = (message.text or "").strip()
    return text in MENU_BUTTONS or text.startswith("/")


def parse_amount(text: Optional[str]) -> Optional[int]:
    """
    "50 000", "50000", "50.000", "50,000" -> 50000.
    Noto'g'ri kiritilgan bo'lsa None qaytaradi.
    """
    if not text:
        return None
    cleaned = re.sub(r"[\s.,']", "", text)
    if not re.fullmatch(r"[0-9]+", cleaned) or len(cleaned) > 12:
        return None
    return int(cleaned)


# Bazada vaqt UTC'da saqlanadi. O'zbekiston vaqti = UTC+5 (yozgi vaqtga o'tilmaydi).
LOCAL_UTC_OFFSET_HOURS = 5


def format_dt(value) -> str:
    """UTC vaqtni O'zbekiston vaqtida '28.09.2026 14:32' ko'rinishida chiqaradi."""
    if value is None:
        return "—"
    return (value + timedelta(hours=LOCAL_UTC_OFFSET_HOURS)).strftime("%d.%m.%Y %H:%M")
