"""
"💰 Balans" bo'limi:
  - joriy balansni ko'rsatish
  - balans to'ldirish jarayoni: summa -> to'lov ko'rsatmasi -> chek rasmi ->
    so'rov bazaga (pending) yoziladi va admin kanaliga yuboriladi.

Balans bilan bog'liq BARCHA biznes-logika backend/services/balance_service.py
da. Bu fayl faqat Telegram suhbatini boshqaradi.
"""

from database import SessionLocal, User, balance_service
import config
from keyboards import CANCEL_BUTTON, balance_menu, cancel_menu, main_menu
from logger import logger
from notifications import send_topup_to_admins
from utils import GENERIC_ERROR, esc, format_price, is_cancel, parse_amount


def _explain(exc: Exception) -> str:
    """Kutilgan xatolikni foydalanuvchiga tushunarli matnga o'giradi."""
    if isinstance(exc, balance_service.UserBlocked):
        return "🚫 Sizning hisobingiz bloklangan.\nYordam uchun administratorga murojaat qiling."
    if isinstance(exc, balance_service.UserNotFound):
        return "❗ Iltimos, avval /start buyrug'ini bosing."
    if isinstance(exc, balance_service.TooManyPendingTopups):
        return (
            f"⏳ Sizda allaqachon {balance_service.MAX_PENDING_TOPUPS} ta ko'rib "
            "chiqilmagan so'rov bor.\nIltimos, administrator javobini kuting."
        )
    if isinstance(exc, balance_service.InvalidAmount):
        return (
            f"❗ Summa {format_price(balance_service.MIN_TOPUP_AMOUNT)} dan "
            f"{format_price(balance_service.MAX_TOPUP_AMOUNT)} gacha bo'lishi kerak."
        )
    return GENERIC_ERROR


def register(bot) -> None:
    def cancel_flow(message):
        bot.send_message(message.chat.id, "↩️ Bekor qilindi.", reply_markup=main_menu(config.WEBSITE_URL))

    # -------------------------------------------------------------
    # Balansni ko'rsatish
    # -------------------------------------------------------------
    @bot.message_handler(func=lambda m: m.text == "💰 Balans")
    def show_balance(message):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
            balance = user.balance if user else None
        except Exception:
            logger.exception("Balansni o'qishda xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR)
            return
        finally:
            db.close()

        if balance is None:
            bot.send_message(message.chat.id, "❗ Iltimos, avval /start buyrug'ini bosing.")
            return

        text = (
            "💰 <b>BALANS</b>\n\n"
            f"💵 Balansingiz:\n{format_price(balance)}\n\n"
            f"🆔 Telegram ID:\n{message.from_user.id}"
        )
        bot.send_message(message.chat.id, text, reply_markup=balance_menu())

    # -------------------------------------------------------------
    # Balans to'ldirish: 1-qadam - summa so'rash
    # -------------------------------------------------------------
    @bot.message_handler(func=lambda m: m.text == "💳 Balans to'ldirish")
    def start_topup(message):
        db = SessionLocal()
        try:
            balance_service.ensure_can_topup(db, message.from_user.id)
        except balance_service.BalanceError as exc:
            bot.send_message(message.chat.id, _explain(exc), reply_markup=main_menu(config.WEBSITE_URL))
            return
        except Exception:
            logger.exception("Balans to'ldirishni boshlashda xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR, reply_markup=main_menu(config.WEBSITE_URL))
            return
        finally:
            db.close()

        sent = bot.send_message(
            message.chat.id,
            "💳 <b>BALANS TO'LDIRISH</b>\n\n"
            "Qancha summa to'ldirmoqchisiz?\n\n"
            "Masalan: <code>50 000</code>\n\n"
            f"Minimal: {format_price(balance_service.MIN_TOPUP_AMOUNT)}\n"
            f"Maksimal: {format_price(balance_service.MAX_TOPUP_AMOUNT)}",
            reply_markup=cancel_menu(),
        )
        bot.register_next_step_handler(sent, process_amount)

    # -------------------------------------------------------------
    # 2-qadam - summani tekshirish va to'lov ko'rsatmasini yuborish
    # -------------------------------------------------------------
    def process_amount(message):
        try:
            if is_cancel(message):
                cancel_flow(message)
                return

            amount = parse_amount(message.text if message.content_type == "text" else None)
            if amount is None:
                sent = bot.send_message(
                    message.chat.id,
                    "❗ Iltimos, summani raqam bilan kiriting.\nMasalan: <code>50 000</code>",
                    reply_markup=cancel_menu(),
                )
                bot.register_next_step_handler(sent, process_amount)
                return

            try:
                balance_service.validate_topup_amount(amount)
            except balance_service.InvalidAmount as exc:
                sent = bot.send_message(
                    message.chat.id, _explain(exc), reply_markup=cancel_menu()
                )
                bot.register_next_step_handler(sent, process_amount)
                return

            if not config.PAYMENT_CARD_NUMBER:
                logger.error("PAYMENT_CARD_NUMBER .env da sozlanmagan")
                bot.send_message(
                    message.chat.id,
                    "⚠️ To'lov ma'lumotlari hozircha sozlanmagan.\n"
                    "Iltimos, administratorga murojaat qiling.",
                    reply_markup=main_menu(config.WEBSITE_URL),
                )
                return

            card_owner = (
                f"\n👤 Karta egasi: {esc(config.PAYMENT_CARD_NAME)}"
                if config.PAYMENT_CARD_NAME
                else ""
            )
            text = (
                "💳 <b>TO'LOV</b>\n\n"
                "Karta:\n"
                f"<code>{esc(config.PAYMENT_CARD_NUMBER)}</code>{card_owner}\n\n"
                "Summa:\n"
                f"{format_price(amount)}\n\n"
                "To'lovni amalga oshirgandan keyin <b>chek rasmini</b> yuboring."
            )
            sent = bot.send_message(message.chat.id, text, reply_markup=cancel_menu())
            bot.register_next_step_handler(sent, process_receipt, amount)
        except Exception:
            logger.exception("Summani qayta ishlashda xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR, reply_markup=main_menu(config.WEBSITE_URL))

    # -------------------------------------------------------------
    # 3-qadam - chek rasmini qabul qilish, so'rov yaratish, adminga yuborish
    # -------------------------------------------------------------
    def process_receipt(message, amount):
        try:
            if is_cancel(message):
                cancel_flow(message)
                return

            if message.content_type != "photo":
                sent = bot.send_message(
                    message.chat.id,
                    "❗ Iltimos, to'lov chekini <b>rasm</b> sifatida yuboring.\n"
                    f"Bekor qilish uchun {CANCEL_BUTTON} tugmasini bosing.",
                    reply_markup=cancel_menu(),
                )
                bot.register_next_step_handler(sent, process_receipt, amount)
                return

            receipt_file_id = message.photo[-1].file_id
            tg_user = message.from_user

            db = SessionLocal()
            try:
                result = balance_service.create_topup_request(
                    db, tg_user.id, amount, receipt_file_id
                )
            except balance_service.BalanceError as exc:
                bot.send_message(message.chat.id, _explain(exc), reply_markup=main_menu(config.WEBSITE_URL))
                return
            finally:
                db.close()

            admin_message_id = send_topup_to_admins(
                bot,
                topup_id=result.topup_id,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                amount=result.amount,
                receipt_file_id=receipt_file_id,
            )

            if admin_message_id is not None:
                db = SessionLocal()
                try:
                    balance_service.set_topup_admin_message(
                        db, result.topup_id, admin_message_id
                    )
                except Exception:
                    logger.exception(
                        "So'rov #%s uchun admin xabar ID'sini saqlashda xatolik",
                        result.topup_id,
                    )
                finally:
                    db.close()

                bot.send_message(
                    message.chat.id,
                    "✅ <b>So'rovingiz qabul qilindi!</b>\n\n"
                    f"🧾 So'rov: #{result.topup_id}\n"
                    f"💵 Summa: {format_price(result.amount)}\n\n"
                    "Administrator tekshirgach, balansingiz to'ldiriladi "
                    "va sizga xabar yuboriladi.",
                    reply_markup=main_menu(config.WEBSITE_URL),
                )
            else:
                bot.send_message(
                    message.chat.id,
                    f"⚠️ So'rovingiz saqlandi (#{result.topup_id}), lekin administratorga "
                    "xabar yuborishda muammo bo'ldi.\n"
                    "Iltimos, administratorga murojaat qiling va so'rov raqamini ayting.",
                    reply_markup=main_menu(config.WEBSITE_URL),
                )
        except Exception:
            logger.exception("Chekni qayta ishlashda xatolik")
            bot.send_message(message.chat.id, GENERIC_ERROR, reply_markup=main_menu(config.WEBSITE_URL))
