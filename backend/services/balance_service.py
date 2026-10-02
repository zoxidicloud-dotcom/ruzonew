"""
Balans bilan bog'liq YAGONA biznes-logika.

Bu fayl HAM Telegram bot, HAM (kelajakda) backend API tomonidan ishlatiladi.
Balansga pul qo'shish/ayirish, to'ldirish so'rovini yaratish/tasdiqlash/rad
etish logikasi FAQAT SHU YERDA yoziladi - boshqa hech qayerda takrorlanmaydi.

QOIDALAR:
  - Bu fayl "config" ni import QILMAYDI (bot va backend'da config.py
    nomi bir xil, lekin ichidagilari boshqa - nom to'qnashuvi bo'lardi).
    Faqat "models" ni import qiladi.
  - Barcha funksiyalar tayyor `db` (SQLAlchemy Session) qabul qiladi va
    o'zi commit/rollback qiladi (apply_balance_change bundan mustasno -
    u chaqiruvchining tranzaksiyasi ichida ishlaydi).

RACE CONDITION HIMOYASI:
  - So'rov holatini o'zgartirish "UPDATE ... WHERE status='pending'" bilan,
    ya'ni bitta atomik SQL buyrug'i bilan qilinadi. Ikkita admin bir vaqtda
    bosganda ham faqat bittasining UPDATE'i 1 ta qatorni o'zgartiradi -
    ikkinchisi 0 qator ko'radi va TopupAlreadyProcessed oladi.
  - Balans "SET balance = balance + X" (atomik SQL ifoda) bilan o'zgaradi -
    Python'da "o'qib, hisoblab, yozib" qilinmaydi.
  - Balans manfiy bo'lib ketishi "WHERE balance + X >= 0" sharti bilan
    bazaning o'zida oldi olinadi.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import update

from models import AdminLog, BalanceTopup, BalanceTransaction, User

# Bir martalik balans to'ldirish limitlari (so'mda)
MIN_TOPUP_AMOUNT = 1000
MAX_TOPUP_AMOUNT = 50000000

# Bitta foydalanuvchida bir vaqtda ko'rib chiqilmagan (pending) so'rovlar
# soni chegarasi (spamdan himoya)
MAX_PENDING_TOPUPS = 3


# ---------------------------------------------------------------------
# Xatoliklar (kutilgan, biznes-darajadagi)
# ---------------------------------------------------------------------
class BalanceError(Exception):
    """Balans logikasidagi kutilgan xatoliklarning asosiy sinfi."""


class InvalidAmount(BalanceError):
    pass


class UserNotFound(BalanceError):
    pass


class UserBlocked(BalanceError):
    pass


class TooManyPendingTopups(BalanceError):
    pass


class TopupNotFound(BalanceError):
    pass


class TopupAlreadyProcessed(BalanceError):
    pass


class InsufficientBalance(BalanceError):
    pass


@dataclass(frozen=True)
class TopupResult:
    topup_id: int
    telegram_id: int
    amount: float
    status: str
    balance_after: Optional[float] = None


# ---------------------------------------------------------------------
# Tekshiruvlar
# ---------------------------------------------------------------------
def validate_topup_amount(amount) -> None:
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise InvalidAmount("Summa raqam bo'lishi kerak")
    if amount < MIN_TOPUP_AMOUNT or amount > MAX_TOPUP_AMOUNT:
        raise InvalidAmount(
            f"Summa {MIN_TOPUP_AMOUNT} dan {MAX_TOPUP_AMOUNT} gacha bo'lishi kerak"
        )


def ensure_can_topup(db, telegram_id: int) -> None:
    """Foydalanuvchi balans to'ldirish so'rovi yubora oladimi - tekshiradi."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user is None:
        raise UserNotFound()
    if user.is_blocked:
        raise UserBlocked()

    pending_count = (
        db.query(BalanceTopup)
        .filter(BalanceTopup.telegram_id == telegram_id, BalanceTopup.status == "pending")
        .count()
    )
    if pending_count >= MAX_PENDING_TOPUPS:
        raise TooManyPendingTopups()


# ---------------------------------------------------------------------
# Balansni atomik o'zgartirish (barcha bosqichlar shu funksiyadan foydalanadi)
# ---------------------------------------------------------------------
def apply_balance_change(
    db,
    telegram_id: int,
    delta: float,
    tx_type: str,
    description: str,
    reference_id: Optional[int] = None,
) -> BalanceTransaction:
    """
    Foydalanuvchi balansini `delta` ga o'zgartiradi (musbat - qo'shish,
    manfiy - ayirish) va balance_transactions ga yozuv qo'shadi.

    DIQQAT: bu funksiya commit QILMAYDI - chaqiruvchi funksiya o'z
    tranzaksiyasini commit/rollback qiladi. Shu sababli, masalan, "so'rov
    holatini o'zgartirish + balansga qo'shish + tranzaksiya yozuvi" birgalikda
    yoki hammasi bajariladi, yoki hech biri.

    tx_type: topup, purchase, refund, admin_add, admin_sub
    """
    result = db.execute(
        update(User)
        .where(User.telegram_id == telegram_id, User.balance + delta >= 0)
        .values(balance=User.balance + delta, updated_at=datetime.utcnow())
        .execution_options(synchronize_session=False)
    )

    if result.rowcount != 1:
        exists = db.query(User.id).filter(User.telegram_id == telegram_id).first()
        if exists is None:
            raise UserNotFound()
        raise InsufficientBalance()

    balance_after = (
        db.query(User.balance).filter(User.telegram_id == telegram_id).scalar()
    )

    transaction = BalanceTransaction(
        telegram_id=telegram_id,
        amount=delta,
        type=tx_type,
        description=description,
        reference_id=reference_id,
        balance_before=balance_after - delta,
        balance_after=balance_after,
    )
    db.add(transaction)
    db.flush()
    return transaction


def _log_admin(db, admin_id: int, action: str, target_id: int, description: str) -> None:
    db.add(
        AdminLog(
            admin_id=admin_id,
            action=action,
            target_id=target_id,
            description=description,
        )
    )


# ---------------------------------------------------------------------
# Balans to'ldirish so'rovlari
# ---------------------------------------------------------------------
def create_topup_request(
    db, telegram_id: int, amount: int, receipt_file_id: str
) -> TopupResult:
    """Yangi 'pending' balans to'ldirish so'rovini yaratadi."""
    validate_topup_amount(amount)
    ensure_can_topup(db, telegram_id)

    try:
        topup = BalanceTopup(
            telegram_id=telegram_id,
            amount=float(amount),
            receipt_file_id=receipt_file_id,
            status="pending",
        )
        db.add(topup)
        db.commit()
        db.refresh(topup)
        return TopupResult(
            topup_id=topup.id,
            telegram_id=topup.telegram_id,
            amount=topup.amount,
            status=topup.status,
        )
    except Exception:
        db.rollback()
        raise


def set_topup_admin_message(db, topup_id: int, message_id: int) -> None:
    """Admin kanaliga yuborilgan xabar ID'sini so'rovga biriktiradi."""
    try:
        db.execute(
            update(BalanceTopup)
            .where(BalanceTopup.id == topup_id)
            .values(admin_message_id=message_id)
            .execution_options(synchronize_session=False)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def approve_topup(db, topup_id: int, admin_telegram_id: int) -> TopupResult:
    """
    So'rovni tasdiqlaydi va foydalanuvchi balansiga summani qo'shadi.

    Ikki marta tasdiqlashdan himoya: "UPDATE ... WHERE status='pending'".
    Faqat 1 ta chaqiruv g'olib bo'ladi, qolganlari TopupAlreadyProcessed oladi.
    """
    try:
        claimed = db.execute(
            update(BalanceTopup)
            .where(BalanceTopup.id == topup_id, BalanceTopup.status == "pending")
            .values(status="approved", approved_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )

        if claimed.rowcount != 1:
            exists = db.query(BalanceTopup.id).filter(BalanceTopup.id == topup_id).first()
            if exists is None:
                raise TopupNotFound()
            raise TopupAlreadyProcessed()

        row = (
            db.query(BalanceTopup.telegram_id, BalanceTopup.amount)
            .filter(BalanceTopup.id == topup_id)
            .one()
        )

        transaction = apply_balance_change(
            db,
            telegram_id=row.telegram_id,
            delta=row.amount,
            tx_type="topup",
            description=f"Balans to'ldirish #{topup_id}",
            reference_id=topup_id,
        )
        balance_after = transaction.balance_after

        _log_admin(
            db,
            admin_telegram_id,
            "topup_approve",
            topup_id,
            f"Balans to'ldirish #{topup_id} tasdiqlandi: +{row.amount:.0f} so'm "
            f"(foydalanuvchi {row.telegram_id})",
        )

        db.commit()
        return TopupResult(
            topup_id=topup_id,
            telegram_id=row.telegram_id,
            amount=row.amount,
            status="approved",
            balance_after=balance_after,
        )
    except Exception:
        db.rollback()
        raise


def reject_topup(
    db, topup_id: int, admin_telegram_id: int, note: Optional[str] = None
) -> TopupResult:
    """So'rovni rad etadi. Balansga hech narsa qo'shilmaydi."""
    try:
        claimed = db.execute(
            update(BalanceTopup)
            .where(BalanceTopup.id == topup_id, BalanceTopup.status == "pending")
            .values(status="rejected", rejected_at=datetime.utcnow(), admin_note=note)
            .execution_options(synchronize_session=False)
        )

        if claimed.rowcount != 1:
            exists = db.query(BalanceTopup.id).filter(BalanceTopup.id == topup_id).first()
            if exists is None:
                raise TopupNotFound()
            raise TopupAlreadyProcessed()

        row = (
            db.query(BalanceTopup.telegram_id, BalanceTopup.amount)
            .filter(BalanceTopup.id == topup_id)
            .one()
        )

        _log_admin(
            db,
            admin_telegram_id,
            "topup_reject",
            topup_id,
            f"Balans to'ldirish #{topup_id} rad etildi: {row.amount:.0f} so'm "
            f"(foydalanuvchi {row.telegram_id})",
        )

        db.commit()
        return TopupResult(
            topup_id=topup_id,
            telegram_id=row.telegram_id,
            amount=row.amount,
            status="rejected",
        )
    except Exception:
        db.rollback()
        raise
