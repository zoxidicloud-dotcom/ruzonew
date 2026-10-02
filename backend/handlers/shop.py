"""
"🛒 Xarid qilish" bo'limi - TO'LIQ buyurtma berish oqimi:

  1. Kategoriya tanlash (🎮 PUBG Mobile va h.k.)
  2. Mahsulot tanlash (inline tugmalar)
  3. Kerakli ma'lumotlarni ketma-ket so'rash (nickname, ID va h.k.)
  4. Tasdiqlash ekrani (barcha ma'lumot + narx + joriy balans)
  5. Tasdiqlansa - buyurtma "pending" holatida bazaga yoziladi va admin
     kanaliga yuboriladi.

Barcha tekshiruvlar (narx, balans, dublikat, limit) backend/services/
order_service.py da - bu fayl faqat Telegram suhbatini boshqaradi.
"""

from telebot import types

from database import Product, SessionLocal, User, order_service
from keyboards import categories_menu, main_menu, cancel_menu
from logger import logger
from notifications import send_order_to_admins
from state import PENDING_ORDERS, PendingOrder, clear_pending_order
from utils import GENERIC_ERROR, esc, format_price, is_cancel

# Menyudagi tugma matni -> database'dagi category qiymati
CATEGORY_SLUGS = {
    "🎮 PUBG Mobile": "pubg",
    "💎 Mobile Legends": "mobile_legends",
    "🔥 Free Fire": "free_fire",
    "⭐ Telegram Stars": "telegram_stars",
    "💎 Telegram Premium": "telegram_premium",
}


def _explain(exc: Exception) -> str:
    """Kutilgan xatolikni foydalanuvchiga tushunarli matnga o'giradi."""
    if isinstance(exc, order_service.UserBlocked):
        return "🚫 Sizning hisobingiz bloklangan.\nYordam uchun administratorga murojaat qiling."
    if isinstance(exc, order_service.UserNotFound):
        return "❗ Iltimos, avval /start buyrug'ini bosing."
    if isinstance(exc, order_service.ProductNotFound):
        return "😕 Bu mahsulot endi mavjud emas. Iltimos, ro'yxatni qayta oching."
    if isinstance(exc, order_service.PriceChanged):
        return "⚠️ Bu mahsulotning narxi o'zgardi. Iltimos, qaytadan tanlang."
    if isinstance(exc, order_service.InsufficientFunds):
        return (
            "❗ Balansingiz yetarli emas.\n\n"
            f"💳 Balansingiz: {format_price(exc.balance)}\n"
            f"💰 Kerak: {format_price(exc.price)}\n\n"
            "Balansni to'ldirish uchun: 💰 Balans → 💳 Balans to'ldirish"
        )
    if isinstance(exc, order_service.TooManyPendingOrders):
        return (
            f"⏳ Sizda allaqachon {order_service.MAX_PENDING_ORDERS} ta ko'rib "
            "chiqilmagan buyurtma bor.\nIltimos, administrator javobini kuting."
        )
    if isinstance(exc, order_service.DuplicateOrder):
        return "⚠️ Bunday buyurtmani hozirgina yubordingiz. Iltimos, biroz kuting."
    if isinstance(exc, order_service.InvalidOrderDetails):
        return "❗ Barcha ma'lumotlar to'ldirilmagan. Iltimos, qaytadan urinib ko'ring."
    return GENERIC_ERROR


def register(bot) -> None:
    def cancel_order_flow(chat_id: int, telegram_id: int) -> None:
        clear_pending_order(telegram_id)
        bot.send_message(chat_id, "↩️ Bekor qilindi.", reply_markup=main_menu())

    # -------------------------------------------------------------
    # 1-qadam: kategoriya tanlash
    # -------------------------------------------------------------
    @bot.message_handler(func=lambda m: m.text == "🛒 Xarid qilish")
    def open_shop(message):
        bot.send_message(
            message.chat.id,
            "🛍 Qaysi mahsulot turini xarid qilmoqchisiz?",
            reply_markup=categories_menu(),
        )

    @bot.message_handler(func=lambda m: m.text in CATEGORY_SLUGS)
    def show_category(message):
        category_slug = CATEGORY_SLUGS[message.text]
        category_info = order_service.get_category(category_slug)

        db = SessionLocal()
        try:
            db_products = (
                db.query(Product)
                .filter(Product.category == category_slug, Product.active == True)  # noqa: E712
                .order_by(Product.sort_order)
                .all()
            )
            products = [(p.id, p.name, p.price) for p in db_products]
        except Exception:
            logger.exception("Mahsulotlar ro'yxatini o'qishda xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR, reply_markup=categories_menu())
            return
        finally:
            db.close()

        if not products:
            bot.send_message(
                message.chat.id,
                "😕 Hozircha bu bo'limda mahsulot mavjud emas.",
                reply_markup=categories_menu(),
            )
            return

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for product_id, name, price in products:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"📦 {name} — 💰 {format_price(price)}",
                    callback_data=f"buy:{product_id}",
                )
            )

        bot.send_message(
            message.chat.id,
            f"{category_info.emoji} <b>{esc(category_info.title)}</b>\n\n"
            "Kerakli paketni tanlang 👇",
            reply_markup=keyboard,
        )

    # -------------------------------------------------------------
    # 2-qadam: mahsulot tanlandi (inline tugma) - ma'lumot so'rashni boshlash
    # -------------------------------------------------------------
    @bot.callback_query_handler(func=lambda c: bool(c.data) and c.data.startswith("buy:"))
    def start_order(call):
        try:
            product_id = int(call.data.split(":", 1)[1])
        except ValueError:
            bot.answer_callback_query(call.id, "❗ Noto'g'ri so'rov.", show_alert=True)
            return

        db = SessionLocal()
        try:
            product = (
                db.query(Product)
                .filter(Product.id == product_id, Product.active == True)  # noqa: E712
                .first()
            )
            if product is None:
                bot.answer_callback_query(
                    call.id, "😕 Bu mahsulot endi mavjud emas.", show_alert=True
                )
                return
            category_slug, price, name = product.category, product.price, product.name
        finally:
            db.close()

        try:
            category_info = order_service.get_category(category_slug)
        except order_service.UnknownCategory:
            logger.error("Noma'lum kategoriya: %s (mahsulot #%s)", category_slug, product_id)
            bot.answer_callback_query(call.id, GENERIC_ERROR, show_alert=True)
            return

        bot.answer_callback_query(call.id)
        PENDING_ORDERS[call.from_user.id] = PendingOrder(
            product_id=product_id,
            category_slug=category_slug,
            expected_price=price,
        )
        bot.send_message(
            call.message.chat.id,
            f"🛒 Siz tanladingiz: <b>{esc(name)}</b> — {format_price(price)}\n\n"
            "Endi kerakli ma'lumotlarni kiritamiz.",
        )
        _ask_field(call.from_user.id, call.message.chat.id, category_info, field_index=0)

    def _ask_field(telegram_id: int, chat_id: int, category_info, field_index: int) -> None:
        if field_index >= len(category_info.fields):
            _show_confirmation(telegram_id, chat_id, category_info)
            return

        field = category_info.fields[field_index]
        sent = bot.send_message(
            chat_id,
            f"{field.emoji} {field.prompt}\nMasalan: <code>{esc(field.example)}</code>",
            reply_markup=cancel_menu(),
        )
        bot.register_next_step_handler(sent, _collect_field, category_info, field_index)

    def _collect_field(message, category_info, field_index: int) -> None:
        telegram_id = message.from_user.id
        chat_id = message.chat.id

        if telegram_id not in PENDING_ORDERS:
            # Foydalanuvchi boshqa buyurtma bilan qayta boshlagan yoki bot
            # qayta ishga tushgan - eski jarayonni davom ettirmaymiz.
            return

        if is_cancel(message):
            cancel_order_flow(chat_id, telegram_id)
            return

        field = category_info.fields[field_index]

        if message.content_type != "text":
            sent = bot.send_message(
                chat_id,
                f"❗ Iltimos, matn ko'rinishida kiriting.\n{field.emoji} {field.prompt}",
                reply_markup=cancel_menu(),
            )
            bot.register_next_step_handler(sent, _collect_field, category_info, field_index)
            return

        try:
            clean_value = field.validator(message.text)
        except order_service.InvalidOrderField as exc:
            sent = bot.send_message(
                chat_id,
                f"❗ {esc(str(exc))}\n\n{field.emoji} {field.prompt}",
                reply_markup=cancel_menu(),
            )
            bot.register_next_step_handler(sent, _collect_field, category_info, field_index)
            return

        PENDING_ORDERS[telegram_id].details[field.key] = clean_value
        _ask_field(telegram_id, chat_id, category_info, field_index + 1)

    # -------------------------------------------------------------
    # 3-qadam: tasdiqlash ekrani
    # -------------------------------------------------------------
    def _show_confirmation(telegram_id: int, chat_id: int, category_info) -> None:
        pending = PENDING_ORDERS.get(telegram_id)
        if pending is None:
            return

        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.id == pending.product_id).first()
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
        finally:
            db.close()

        if product is None or user is None:
            clear_pending_order(telegram_id)
            bot.send_message(chat_id, GENERIC_ERROR, reply_markup=main_menu())
            return

        lines = [
            "🛒 <b>BUYURTMANI TASDIQLASH</b>",
            "",
            f"{category_info.kind_emoji} {category_info.kind_label}:",
            esc(category_info.title),
            "",
        ]
        for field in category_info.fields:
            value = pending.details.get(field.key)
            if value:
                lines += [f"{field.emoji} {esc(field.label)}:", esc(value), ""]

        lines += [
            "📦 Xarid:",
            esc(product.name),
            "",
            "💰 Narx:",
            format_price(product.price),
            "",
            "💳 Balans:",
            format_price(user.balance),
        ]

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="order:confirm"),
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="order:cancel"),
        )
        bot.send_message(chat_id, "\n".join(lines), reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda c: c.data == "order:cancel")
    def cancel_confirmation(call):
        bot.answer_callback_query(call.id)
        cancel_order_flow(call.message.chat.id, call.from_user.id)

    # -------------------------------------------------------------
    # 4-qadam: yakuniy tasdiqlash - buyurtmani yaratish
    # -------------------------------------------------------------
    @bot.callback_query_handler(func=lambda c: c.data == "order:confirm")
    def confirm_order(call):
        telegram_id = call.from_user.id
        pending = PENDING_ORDERS.get(telegram_id)
        if pending is None:
            bot.answer_callback_query(
                call.id, "⚠️ Bu buyurtma muddati o'tgan. Iltimos, qaytadan boshlang.",
                show_alert=True,
            )
            return

        db = SessionLocal()
        try:
            result = order_service.create_order(
                db,
                telegram_id,
                pending.product_id,
                pending.details,
                expected_price=pending.expected_price,
            )
        except order_service.OrderError as exc:
            bot.answer_callback_query(call.id)
            clear_pending_order(telegram_id)
            bot.send_message(call.message.chat.id, _explain(exc), reply_markup=main_menu())
            return
        except Exception:
            logger.exception("Buyurtma yaratishda kutilmagan xatolik")
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, GENERIC_ERROR, reply_markup=main_menu())
            return
        finally:
            db.close()

        clear_pending_order(telegram_id)
        bot.answer_callback_query(call.id, "✅ Buyurtma qabul qilindi!")

        bot.send_message(
            call.message.chat.id,
            "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
            f"🧾 Buyurtma: #{result.order_number}\n"
            f"📦 {esc(result.product_name)}\n"
            f"💰 {format_price(result.price)}\n\n"
            "Administrator tez orada ko'rib chiqadi. Holatini \"📦 Buyurtmalarim\" "
            "bo'limidan kuzatib borishingiz mumkin.",
            reply_markup=main_menu(),
        )

        send_order_to_admins(bot, result, call.from_user.username, call.from_user.first_name)
