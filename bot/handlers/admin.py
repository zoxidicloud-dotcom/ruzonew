"""
Admin amallari (inline tugmalar): balans to'ldirish so'rovlarini
✅ TASDIQLASH / ❌ RAD ETISH.

Xavfsizlik:
  - Tugmani faqat .env dagi ADMIN_TELEGRAM_IDS ro'yxatidagi foydalanuvchilar
    bosa oladi (kanalni boshqalar ko'rsa ham, ular bosa olmaydi).
  - Ikki marta bosish/ikki admin bir vaqtda bosishdan himoya
    balance_service ichida (atomik UPDATE ... WHERE status='pending').
"""

from telebot import types

from database import AdminLog, BalanceTopup, SessionLocal, User, balance_service, order_service
import config
from logger import logger
from notifications import order_admin_keyboard, order_caption, topup_caption
from utils import esc, format_price


def _admin_display_name(tg_user) -> str:
    if tg_user.username:
        return f"@{tg_user.username}"
    return tg_user.first_name or str(tg_user.id)


def _edit_admin_message(bot, call, caption: str) -> None:
    """Admin xabarining (rasmli, balans so'rovi) matnini yangilaydi."""
    try:
        bot.edit_message_caption(
            caption=caption,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup(),
        )
    except Exception:
        logger.warning("Admin xabarini yangilab bo'lmadi", exc_info=True)


def _edit_order_message(bot, call, text: str, keyboard=None) -> None:
    """Admin xabarining (matnli, buyurtma) matnini va tugmalarini yangilaydi."""
    try:
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard or types.InlineKeyboardMarkup(),
        )
    except Exception:
        logger.warning("Buyurtma xabarini yangilab bo'lmadi", exc_info=True)


def _notify_user(bot, telegram_id: int, text: str) -> bool:
    try:
        bot.send_message(telegram_id, text)
        return True
    except Exception:
        logger.warning("Foydalanuvchi %s ga xabar yuborib bo'lmadi", telegram_id, exc_info=True)
        return False


def _process_topup_action(bot, call) -> None:
    if call.from_user.id not in config.ADMIN_TELEGRAM_IDS:
        logger.warning(
            "Ruxsatsiz urinish: %s (@%s) admin tugmasini bosdi",
            call.from_user.id,
            call.from_user.username,
        )
        bot.answer_callback_query(call.id, "⛔ Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return

    parts = (call.data or "").split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        bot.answer_callback_query(call.id, "❗ Noto'g'ri so'rov.", show_alert=True)
        return

    action = parts[1]
    topup_id = int(parts[2])
    already_processed = False
    result = None

    db = SessionLocal()
    try:
        try:
            if action == "approve":
                result = balance_service.approve_topup(db, topup_id, call.from_user.id)
            else:
                result = balance_service.reject_topup(db, topup_id, call.from_user.id)
        except balance_service.TopupNotFound:
            bot.answer_callback_query(call.id, "❗ So'rov topilmadi.", show_alert=True)
            return
        except balance_service.TopupAlreadyProcessed:
            already_processed = True

        if already_processed:
            topup = db.query(BalanceTopup).filter(BalanceTopup.id == topup_id).first()
            telegram_id, amount, status = topup.telegram_id, topup.amount, topup.status
        else:
            telegram_id, amount, status = result.telegram_id, result.amount, result.status

        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        username = user.username if user else None
        first_name = user.first_name if user else None
    finally:
        db.close()

    if already_processed:
        bot.answer_callback_query(
            call.id, "ℹ️ Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True
        )
        _edit_admin_message(
            bot,
            call,
            topup_caption(topup_id, telegram_id, username, first_name, amount, status),
        )
        return

    admin_name = _admin_display_name(call.from_user)
    _edit_admin_message(
        bot,
        call,
        topup_caption(
            topup_id, telegram_id, username, first_name, amount, status, admin_name
        ),
    )

    if action == "approve":
        user_text = (
            "✅ <b>Balansingiz muvaffaqiyatli to'ldirildi.</b>\n\n"
            f"💰 +{format_price(amount)}\n\n"
            "💳 Joriy balans:\n"
            f"{format_price(result.balance_after)}"
        )
        answer = "✅ Tasdiqlandi. Balansga qo'shildi."
    else:
        user_text = (
            "❌ <b>Balans to'ldirish so'rovingiz rad etildi.</b>\n\n"
            f"💵 Summa: {format_price(amount)}\n\n"
            "Savollar bo'lsa, administrator bilan bog'laning."
        )
        answer = "❌ Rad etildi."

    delivered = _notify_user(bot, telegram_id, user_text)
    if not delivered:
        answer += " (Foydalanuvchiga xabar yuborilmadi.)"
    bot.answer_callback_query(call.id, answer)


def _order_user_message(action: str, order) -> str:
    """
    Buyurtma holati o'zgarganda foydalanuvchiga yuboriladigan xabar matni.
    `order` - order_service.OrderActionResult.
    """
    if action == "approve":
        return (
            "✅ <b>Buyurtmangiz tasdiqlandi.</b>\n\n"
            f"📦 {esc(order.product_name)}\n"
            f"💰 -{format_price(order.price)}\n\n"
            "Administrator tez orada mahsulotni yuboradi."
        )
    if action == "reject":
        return (
            "❌ <b>Buyurtmangiz rad etildi.</b>\n\n"
            f"📦 {esc(order.product_name)}\n\n"
            "Balansingizdan hech narsa yechilmagan edi.\n"
            "Savollar bo'lsa, administrator bilan bog'laning."
        )
    if action == "complete":
        category = order_service.get_category(order.category)
        return (
            "✅ <b>BUYURTMANGIZ BAJARILDI</b>\n\n"
            "📦 Mahsulot:\n"
            f"{esc(order.product_name)}\n\n"
            f"{category.kind_emoji} {esc(category.title)}\n\n"
            "Rahmat!"
        )
    # refund
    return (
        "↩️ <b>Buyurtma bekor qilindi.</b>\n\n"
        f"💰 +{format_price(order.price)} balansingizga qaytarildi."
    )


def _process_order_action(bot, call) -> None:
    if call.from_user.id not in config.ADMIN_TELEGRAM_IDS:
        logger.warning(
            "Ruxsatsiz urinish: %s (@%s) buyurtma tugmasini bosdi",
            call.from_user.id,
            call.from_user.username,
        )
        bot.answer_callback_query(call.id, "⛔ Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return

    parts = (call.data or "").split(":")
    valid_actions = ("approve", "reject", "complete", "refund")
    if len(parts) != 3 or parts[1] not in valid_actions or not parts[2].isdigit():
        bot.answer_callback_query(call.id, "❗ Noto'g'ri so'rov.", show_alert=True)
        return

    action = parts[1]
    order_id = int(parts[2])

    db = SessionLocal()
    try:
        already_processed = False
        try:
            if action == "approve":
                order = order_service.claim_order_approval(db, order_id)
                balance_service.apply_balance_change(
                    db, order.telegram_id, -order.price, "purchase",
                    f"Buyurtma #{order.order_number}", reference_id=order.order_id,
                )
            elif action == "reject":
                order = order_service.claim_order_rejection(db, order_id)
            elif action == "complete":
                order = order_service.claim_order_completion(db, order_id)
            else:  # refund
                order = order_service.claim_order_refund(db, order_id)
                balance_service.apply_balance_change(
                    db, order.telegram_id, order.price, "refund",
                    f"Buyurtma #{order.order_number} qaytarildi", reference_id=order.order_id,
                )

            db.add(
                AdminLog(
                    admin_id=call.from_user.id,
                    action=f"order_{action}",
                    target_id=order_id,
                    description=f"Buyurtma #{order.order_number}: {action}",
                )
            )
            db.commit()
        except (order_service.OrderNotFound, order_service.OrderNotPending, order_service.OrderNotApproved):
            db.rollback()
            already_processed = True
            order = order_service.get_order_result(db, order_id)
        except balance_service.InsufficientBalance:
            db.rollback()
            bot.answer_callback_query(
                call.id,
                "❗ Foydalanuvchi balansi yetarli emas (boshqa buyurtma bilan sarflab "
                "yuborgan bo'lishi mumkin). Buyurtma holati o'zgartirilmadi.",
                show_alert=True,
            )
            return

        user = db.query(User).filter(User.telegram_id == order.telegram_id).first()
        username = user.username if user else None
        first_name = user.first_name if user else None
    finally:
        db.close()

    if already_processed:
        bot.answer_callback_query(
            call.id, "ℹ️ Bu buyurtma allaqachon ko'rib chiqilgan.", show_alert=True
        )
        _edit_order_message(
            bot, call,
            order_caption(order, username, first_name),
            order_admin_keyboard(order_id, order.status),
        )
        return

    admin_name = _admin_display_name(call.from_user)
    _edit_order_message(
        bot, call,
        order_caption(order, username, first_name, admin_name),
        order_admin_keyboard(order_id, order.status),
    )

    delivered = _notify_user(bot, order.telegram_id, _order_user_message(action, order))
    answer_map = {
        "approve": "✅ Tasdiqlandi. Balansdan yechildi.",
        "reject": "❌ Rad etildi.",
        "complete": "✅ Bajarildi deb belgilandi.",
        "refund": "↩️ Balansga qaytarildi.",
    }
    answer = answer_map[action]
    if not delivered:
        answer += " (Foydalanuvchiga xabar yuborilmadi.)"
    bot.answer_callback_query(call.id, answer)


def register(bot) -> None:
    @bot.callback_query_handler(func=lambda c: bool(c.data) and c.data.startswith("topup:"))
    def handle_topup_action(call):
        try:
            _process_topup_action(bot, call)
        except Exception:
            logger.exception("Admin tugmasini qayta ishlashda xatolik: %s", call.data)
            try:
                bot.answer_callback_query(
                    call.id,
                    "❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
                    show_alert=True,
                )
            except Exception:
                logger.warning("Callback'ga javob berib bo'lmadi", exc_info=True)

    @bot.callback_query_handler(func=lambda c: bool(c.data) and c.data.startswith("oadmin:"))
    def handle_order_action(call):
        try:
            _process_order_action(bot, call)
        except Exception:
            logger.exception("Buyurtma admin amalida xatolik: %s", call.data)
            try:
                bot.answer_callback_query(
                    call.id,
                    "❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
                    show_alert=True,
                )
            except Exception:
                logger.warning("Callback'ga javob berib bo'lmadi", exc_info=True)
