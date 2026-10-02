"""
Gaming Shop - Telegram bot.

Ishga tushirish (bot/ papkasi ichida turib):
    python bot.py
"""

import telebot

import config
from database import Base, engine
from logger import logger


class LogExceptionHandler(telebot.ExceptionHandler):
    """Handler ichidagi kutilmagan xatoliklarni logs/error.log ga yozadi."""

    def handle(self, exception):
        logger.error("Handlerda kutilmagan xatolik", exc_info=exception)
        return True


# Jadvallarni yaratish (agar hali mavjud bo'lmasa). Backend allaqachon
# yaratgan bo'lsa, bu qator hech narsa qilmaydi.
Base.metadata.create_all(bind=engine)

bot = telebot.TeleBot(
    config.BOT_TOKEN,
    parse_mode="HTML",
    exception_handler=LogExceptionHandler(),
)

# Handlerlarni ro'yxatdan o'tkazish tartibi MUHIM:
# "common" eng oxirida turishi kerak, chunki u ichidagi fallback handler
# barcha mos kelmagan matnlarni ushlab qoladi.
from handlers import admin, balance, common, orders, profile, shop, start  # noqa: E402

start.register(bot)
shop.register(bot)
balance.register(bot)
profile.register(bot)
orders.register(bot)
admin.register(bot)
common.register(bot)


if __name__ == "__main__":
    logger.info("%s boti ishga tushmoqda...", config.SHOP_NAME)
    print("To'xtatish uchun: Ctrl + C")
    bot.infinity_polling(skip_pending=True)
