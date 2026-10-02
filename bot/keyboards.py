"""Botning ReplyKeyboard menyulari."""

from telebot import types

CANCEL_BUTTON = "❌ Bekor qilish"

# Barcha menyu tugmalari matni. Ko'p bosqichli jarayon (masalan, summa
# kiritish) paytida foydalanuvchi menyu tugmasini bossa, jarayon bekor
# qilinishi uchun kerak.
MENU_BUTTONS = {
    "🛒 Xarid qilish",
    "💰 Balans",
    "📦 Buyurtmalarim",
    "👤 Profil",
    "🎁 Promo",
    "👥 Referral",
    "💬 Yordam",
    "🎮 PUBG Mobile",
    "💎 Mobile Legends",
    "🔥 Free Fire",
    "⭐ Telegram Stars",
    "💎 Telegram Premium",
    "💳 Balans to'ldirish",
    "⬅️ Orqaga",
    "🌐 Saytni ochish",
    CANCEL_BUTTON,
}


def main_menu(website_url: str = "") -> types.ReplyKeyboardMarkup:
    """
    Asosiy menyu (loyiha talabidagi 6-band bo'yicha).

    `website_url` berilgan va https:// bilan boshlansa, qo'shimcha
    "🌐 Saytni ochish" tugmasi qo'shiladi - bosilganda sayt Telegram
    ICHIDA (Mini App sifatida) ochiladi. Telegram web_app tugmalari uchun
    FAQAT https:// manzillarni qabul qiladi (http://localhost ishlamaydi) -
    shuning uchun bu shart tekshiriladi.
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🛒 Xarid qilish"),
        types.KeyboardButton("💰 Balans"),
    )
    kb.add(
        types.KeyboardButton("📦 Buyurtmalarim"),
        types.KeyboardButton("👤 Profil"),
    )
    kb.add(
        types.KeyboardButton("🎁 Promo"),
        types.KeyboardButton("👥 Referral"),
    )
    if website_url.startswith("https://"):
        kb.add(
            types.KeyboardButton("💬 Yordam"),
            types.KeyboardButton("🌐 Saytni ochish", web_app=types.WebAppInfo(url=website_url)),
        )
    else:
        kb.add(types.KeyboardButton("💬 Yordam"))
    return kb


def categories_menu() -> types.ReplyKeyboardMarkup:
    """Xarid qilish bosilganda chiqadigan kategoriyalar menyusi."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(types.KeyboardButton("🎮 PUBG Mobile"))
    kb.add(types.KeyboardButton("💎 Mobile Legends"))
    kb.add(types.KeyboardButton("🔥 Free Fire"))
    kb.add(types.KeyboardButton("⭐ Telegram Stars"))
    kb.add(types.KeyboardButton("💎 Telegram Premium"))
    kb.add(types.KeyboardButton("⬅️ Orqaga"))
    return kb


def balance_menu() -> types.ReplyKeyboardMarkup:
    """Balans bo'limidagi submenyu."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(types.KeyboardButton("💳 Balans to'ldirish"))
    kb.add(types.KeyboardButton("⬅️ Orqaga"))
    return kb


def cancel_menu() -> types.ReplyKeyboardMarkup:
    """Ko'p bosqichli jarayon paytida ko'rsatiladigan 'Bekor qilish' menyusi."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(types.KeyboardButton(CANCEL_BUTTON))
    return kb
