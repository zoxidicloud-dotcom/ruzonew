"""
"📦 Buyurtmalarim" bo'limi: foydalanuvchining oxirgi buyurtmalari ro'yxati.
"""

from database import SessionLocal, order_service
from logger import logger
from notifications import ORDER_STATUS_LABELS
from utils import GENERIC_ERROR, esc, format_price

CATEGORY_TITLES = {
    slug: f"{info.emoji} {info.title}" for slug, info in order_service.CATEGORIES.items()
}


def register(bot) -> None:
    @bot.message_handler(func=lambda m: m.text == "📦 Buyurtmalarim")
    def show_orders(message):
        db = SessionLocal()
        try:
            orders = order_service.list_user_orders(db, message.from_user.id, limit=10)
        except Exception:
            logger.exception("Buyurtmalar tarixini o'qishda xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR)
            return
        finally:
            db.close()

        if not orders:
            bot.send_message(
                message.chat.id,
                "📦 Sizda hali buyurtmalar yo'q.\n\nXarid qilish uchun: 🛒 Xarid qilish",
            )
            return

        lines = ["📦 <b>BUYURTMALARIM</b>", ""]
        for order in orders:
            category_title = CATEGORY_TITLES.get(order.category, esc(order.category))
            status_label = ORDER_STATUS_LABELS.get(order.status, esc(order.status))
            date_text = (
                order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "—"
            )
            lines += [
                f"<b>#{esc(order.order_number)}</b>",
                category_title,
                f"📦 {esc(order.product_name)}",
                f"💰 {format_price(order.price)}",
                f"📌 {status_label}",
                f"📅 {date_text}",
                "",
            ]

        bot.send_message(message.chat.id, "\n".join(lines).strip())
