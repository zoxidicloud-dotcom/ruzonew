"""
/start buyrug'ini qayta ishlash: foydalanuvchini bazaga yozish (yoki
mavjud bo'lsa - ma'lumotlarini yangilash) va asosiy menyuni ko'rsatish.

Foydalanuvchini ro'yxatdan o'tkazish logikasi endi database.py bridge
orqali yuklangan umumiy `user_service`da (backend/services/user_service.py) -
buni backend ham (Telegram Mini App autentifikatsiyasi, 6-bosqich) xuddi
shu funksiyadan foydalanadi, shuning uchun ikkala joyda alohida-alohida
yozilmagan.

ESLATMA: Referral kodini /start orqali qabul qilish (masalan
"/start REF12345") - 8-bosqichda qo'shiladi. Hozircha har bir foydalanuvchi
uchun o'zining referral_code'i yaratiladi, lekin referal bog'lash logikasi
hali yozilmagan.
"""

from database import SessionLocal, user_service
import config
from keyboards import main_menu
from logger import logger
from utils import GENERIC_ERROR, esc


def register(bot) -> None:
    @bot.message_handler(commands=["start"])
    def handle_start(message):
        tg_user = message.from_user
        is_env_admin = tg_user.id in config.ADMIN_TELEGRAM_IDS

        db = SessionLocal()
        try:
            user = user_service.get_or_create_user(
                db,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                is_admin=is_env_admin,
            )
            is_blocked = user.is_blocked
        except Exception:
            db.rollback()
            logger.exception("/start da xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR)
            return
        finally:
            db.close()

        if is_blocked:
            bot.send_message(
                message.chat.id,
                "🚫 Sizning hisobingiz bloklangan.\n"
                "Yordam uchun administratorga murojaat qiling.",
            )
            return

        name = esc(tg_user.first_name) or "do'stim"
        text = (
            f"👋 Assalomu alaykum, {name}!\n\n"
            f"🎮 <b>{esc(config.SHOP_NAME)}</b> do'koniga xush kelibsiz!\n\n"
            "Bu yerda siz quyidagi mahsulotlarni sotib olishingiz mumkin:\n"
            "🎮 PUBG Mobile UC\n"
            "💎 Mobile Legends Diamonds\n"
            "🔥 Free Fire Diamonds\n"
            "⭐ Telegram Stars\n"
            "💎 Telegram Premium\n\n"
            "Quyidagi menyudan foydalaning 👇"
        )
        bot.send_message(message.chat.id, text, reply_markup=main_menu(config.WEBSITE_URL))
