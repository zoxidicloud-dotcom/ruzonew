"""
"👤 Profil" bo'limi: foydalanuvchi haqidagi umumiy ma'lumotlarni ko'rsatadi.
"""

from database import Order, SessionLocal, User
from utils import format_price


def register(bot) -> None:
    @bot.message_handler(func=lambda m: m.text == "👤 Profil")
    def show_profile(message):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
            if not user:
                bot.send_message(message.chat.id, "❗ Iltimos, avval /start buyrug'ini bosing.")
                return

            orders_count = (
                db.query(Order).filter(Order.telegram_id == user.telegram_id).count()
            )
            referrals_count = db.query(User).filter(User.referred_by == user.id).count()

            username = user.username
            balance = user.balance
            telegram_id = user.telegram_id
            created_at = user.created_at
        finally:
            db.close()

        username_text = f"@{username}" if username else "— (username yo'q)"
        registered_date = created_at.strftime("%d.%m.%Y") if created_at else "—"

        text = (
            "👤 <b>PROFIL</b>\n\n"
            f"🆔 Telegram ID:\n{telegram_id}\n\n"
            f"👤 Username:\n{username_text}\n\n"
            f"💰 Balans:\n{format_price(balance)}\n\n"
            f"📦 Buyurtmalar soni:\n{orders_count}\n\n"
            f"👥 Taklif qilganlar soni:\n{referrals_count}\n\n"
            f"📅 Ro'yxatdan o'tgan sana:\n{registered_date}"
        )
        bot.send_message(message.chat.id, text)
