"""
Admin kanaliga (yoki adminlarga) xabar yuborish va admin xabarlarini
formatlash: balans to'ldirish so'rovlari va yangi buyurtmalar uchun.
"""

from typing import Callable, Optional, Union

from telebot import types

import config
from database import order_service
from logger import logger
from utils import esc, format_price

STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "approved": "✅ Tasdiqlandi",
    "rejected": "❌ Rad etildi",
}


def parse_chat_id(raw: str) -> Optional[Union[int, str]]:
    """
    .env dagi ADMIN_CHANNEL_ID ni Telegram chat_id ga o'giradi.
    "-1001234567890" -> int, "@kanal_nomi" -> str, bo'sh -> None
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.lstrip("-").isdigit():
        return int(raw)
    return raw


def _user_text(username: Optional[str], first_name: Optional[str]) -> str:
    if username:
        return f"@{esc(username)}"
    if first_name:
        return f"{esc(first_name)} (username yo'q)"
    return "— (username yo'q)"


def _deliver_to_admins(bot, send: Callable, what: str) -> Optional[int]:
    """
    `send(chat_id)` funksiyasi yordamida xabarni avval admin kanaliga yuboradi.
    Kanalga yuborib bo'lmasa, zaxira yo'l sifatida har bir adminga shaxsiy xabar
    yuboradi. Yuborilgan xabar ID'sini qaytaradi (hech qayerga bormasa - None).
    """
    channel_id = parse_chat_id(config.ADMIN_CHANNEL_ID)
    if channel_id is not None:
        try:
            return send(channel_id).message_id
        except Exception:
            logger.exception(
                "%s: admin kanaliga yuborib bo'lmadi (ADMIN_CHANNEL_ID=%s). "
                "Adminlarga shaxsiy xabar yuborishga urinilmoqda.",
                what,
                config.ADMIN_CHANNEL_ID,
            )

    first_message_id: Optional[int] = None
    for admin_id in config.ADMIN_TELEGRAM_IDS:
        try:
            message = send(admin_id)
            if first_message_id is None:
                first_message_id = message.message_id
        except Exception:
            logger.exception("%s: admin %s ga shaxsiy xabar yuborib bo'lmadi", what, admin_id)

    if first_message_id is None:
        logger.error("%s HECH BIR adminga yuborilmadi", what)
    return first_message_id


# ---------------------------------------------------------------------
# Balans to'ldirish
# ---------------------------------------------------------------------
def topup_caption(
    topup_id: int,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    amount: float,
    status: str,
    admin_name: Optional[str] = None,
) -> str:
    lines = [
        f"💰 <b>BALANS TO'LDIRISH #{topup_id}</b>",
        "",
        "👤 Foydalanuvchi:",
        _user_text(username, first_name),
        "",
        "🆔 Telegram ID:",
        f"<code>{telegram_id}</code>",
        "",
        "💵 Summa:",
        format_price(amount),
        "",
        "📌 Status:",
        STATUS_LABELS.get(status, esc(status)),
    ]
    if admin_name:
        lines += ["", f"👮 Admin: {esc(admin_name)}"]
    return "\n".join(lines)


def topup_admin_keyboard(topup_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ TASDIQLASH", callback_data=f"topup:approve:{topup_id}"),
        types.InlineKeyboardButton("❌ RAD ETISH", callback_data=f"topup:reject:{topup_id}"),
    )
    return kb


def send_topup_to_admins(
    bot,
    topup_id: int,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    amount: float,
    receipt_file_id: str,
) -> Optional[int]:
    caption = topup_caption(topup_id, telegram_id, username, first_name, amount, "pending")
    keyboard = topup_admin_keyboard(topup_id)

    def send(chat_id):
        return bot.send_photo(
            chat_id,
            receipt_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    return _deliver_to_admins(bot, send, f"Balans so'rovi #{topup_id}")


# ---------------------------------------------------------------------
# Yangi buyurtma va admin amallari (4-bosqich: TASDIQLASH / BAJARILDI /
# RAD ETISH / QAYTARISH)
# ---------------------------------------------------------------------
ORDER_STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "approved": "✅ Tasdiqlangan",
    "processing": "⚙️ Jarayonda",
    "completed": "✅ Bajarildi",
    "rejected": "❌ Rad etilgan",
    "refunded": "↩️ Qaytarilgan",
}


def order_caption(
    order_result,
    username: Optional[str],
    first_name: Optional[str],
    admin_name: Optional[str] = None,
) -> str:
    """
    Admin kanalidagi buyurtma xabarining matni. `order_result` - shu
    buyurtmaning HOZIRGI holatini aks ettiruvchi obyekt (order_service dagi
    OrderResult yoki OrderActionResult - ikkalasida ham bir xil maydonlar
    bor). Qaysi tafsilot maydonlari (nickname, game_id, ...) ko'rsatilishi
    kerakligi order_service.CATEGORIES dagi kategoriya ta'rifidan olinadi.
    """
    category = order_service.get_category(order_result.category)

    detail_values = {
        "nickname": order_result.nickname,
        "game_id": order_result.game_id,
        "zone_id": order_result.zone_id,
        "target_username": order_result.target_username,
    }

    lines = [
        f"🛒 <b>BUYURTMA #{esc(order_result.order_number)}</b>",
        "",
        f"{category.kind_emoji} {category.kind_label}:",
        esc(category.title),
        "",
    ]

    for field in category.fields:
        value = detail_values.get(field.key)
        if value:
            lines += [f"{field.emoji} {esc(field.admin_label)}:", esc(value), ""]

    lines += [
        "👤 Foydalanuvchi:",
        _user_text(username, first_name),
        "",
        "🆔 Telegram ID:",
        f"<code>{order_result.telegram_id}</code>",
        "",
        "📦 Xarid:",
        esc(order_result.product_name),
        "",
        "💰 Narx:",
        format_price(order_result.price),
        "",
        "📌 Status:",
        ORDER_STATUS_LABELS.get(order_result.status, esc(order_result.status)),
    ]
    if admin_name:
        lines += ["", f"👮 Admin: {esc(admin_name)}"]
    return "\n".join(lines)


def order_admin_keyboard(order_id: int, status: str) -> Optional[types.InlineKeyboardMarkup]:
    """
    Buyurtmaning HOZIRGI holatiga mos tugmalarni qaytaradi:
      pending  -> TASDIQLASH / RAD ETISH
      approved -> BAJARILDI / QAYTARISH
      boshqa (completed/rejected/refunded) -> tugma yo'q (yakuniy holat)
    """
    if status == "pending":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✅ TASDIQLASH", callback_data=f"oadmin:approve:{order_id}"),
            types.InlineKeyboardButton("❌ RAD ETISH", callback_data=f"oadmin:reject:{order_id}"),
        )
        return kb
    if status == "approved":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("⚙️ BAJARILDI", callback_data=f"oadmin:complete:{order_id}"),
            types.InlineKeyboardButton("↩️ QAYTARISH", callback_data=f"oadmin:refund:{order_id}"),
        )
        return kb
    return None


def send_order_to_admins(bot, order_result, username: Optional[str], first_name: Optional[str]) -> Optional[int]:
    """Yangi ('pending') buyurtmani adminlarga yuboradi. Xabar ID'sini qaytaradi."""
    caption = order_caption(order_result, username, first_name)
    keyboard = order_admin_keyboard(order_result.order_id, "pending")

    def send(chat_id):
        return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)

    return _deliver_to_admins(bot, send, f"Buyurtma #{order_result.order_number}")
