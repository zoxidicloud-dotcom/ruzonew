"""
Umumiy handlerlar: "Orqaga", "Yordam", "Bekor qilish" va hali ishlab
chiqilmagan bo'limlar (Promo, Referral) uchun ma'lumot xabarlari,
shuningdek noma'lum matnlar uchun "fallback" handler.

MUHIM: bu fayldagi handlerlar ENG OXIRIDA ro'yxatdan o'tkazilishi kerak
(bot.py ichida), chunki fallback handler (eng pastda) barcha matnlarni
ushlab qoladi - u faqat boshqa hech qanday handler mos kelmagan holatlarda
ishga tushishi kerak. pyTelegramBotAPI har bir xabar uchun handlerlarni
ro'yxatga olingan tartibda tekshiradi va BIRINCHI mos kelgan handlerni
ishga tushirib, keyingilarini tekshirmaydi.
"""

import config
from keyboards import CANCEL_BUTTON, main_menu


def register(bot) -> None:
    @bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
    def go_back(message):
        bot.send_message(message.chat.id, "🏠 Bosh menyu", reply_markup=main_menu(config.WEBSITE_URL))

    @bot.message_handler(func=lambda m: m.text == CANCEL_BUTTON)
    def stale_cancel(message):
        # Jarayon allaqachon tugagan (yoki bot qayta ishga tushgan) bo'lsa,
        # eski "Bekor qilish" tugmasi bosilganda asosiy menyuga qaytaramiz.
        bot.send_message(message.chat.id, "🏠 Bosh menyu", reply_markup=main_menu(config.WEBSITE_URL))

    @bot.message_handler(func=lambda m: m.text == "💬 Yordam")
    def show_help(message):
        text = (
            "💬 <b>YORDAM</b>\n\n"
            "Savol yoki muammo bo'lsa, administratorga murojaat qiling.\n\n"
            "Buyruqlar:\n"
            "/start — Botni qayta ishga tushirish"
        )
        bot.send_message(message.chat.id, text)

    @bot.message_handler(func=lambda m: m.text == "🎁 Promo")
    def promo_notice(message):
        bot.send_message(
            message.chat.id,
            "ℹ️ Promo kod funksiyasi keyingi bosqichlarda faollashtiriladi.",
        )

    @bot.message_handler(func=lambda m: m.text == "👥 Referral")
    def referral_notice(message):
        bot.send_message(
            message.chat.id,
            "ℹ️ Referral tizimi keyingi bosqichlarda faollashtiriladi.",
        )

    # FALLBACK: yuqoridagi (va boshqa fayllardagi) hech qanday handlerga mos
    # kelmagan har qanday matnli xabar shu yerda ushlanadi. Shu sababli bu
    # handler ENG OXIRGI bo'lib ro'yxatdan o'tkazilishi shart.
    @bot.message_handler(content_types=["text"])
    def fallback(message):
        bot.send_message(
            message.chat.id,
            "❓ Kechirasiz, bu buyruqni tushunmadim.\n"
            "Iltimos, pastdagi menyudan foydalaning.",
        )
