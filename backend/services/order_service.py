"""
Buyurtmalar bilan bog'liq YAGONA biznes-logika.

Bot ham, (kelajakda) sayt/API ham buyurtmani FAQAT shu servis orqali yaratadi.
Mahsulot turlari (PUBG, Mobile Legends, ...) uchun qanday ma'lumotlar
so'ralishi, ular qanday tekshirilishi - hammasi shu yerda (CATEGORIES).

BIZNES-QOIDA: buyurtma yaratilganda balansdan pul YECHILMAYDI. Buyurtma
"pending" holatida yaratiladi, balans esa admin buyurtmani tasdiqlaganda
yechiladi (4-bosqich). Buyurtma yaratishda faqat balans YETARLIMI - shu
tekshiriladi.

QOIDALAR:
  - "config" import QILINMAYDI (bot va backend'da nom to'qnashuvi bo'ladi).
  - Funksiyalar tayyor `db` (SQLAlchemy Session) oladi va o'zi commit/rollback qiladi.

DUBLIKATDAN HIMOYA: create_order boshida foydalanuvchi qatoriga "bo'sh" UPDATE
qilinadi - bu SQLite'da yozish qulfini oladi. Shundan keyingi tekshiruvlar
(dublikat, limit) va INSERT boshqa parallel so'rovlar bilan aralashmaydi.
"""

import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import update

from models import Order, Product, User

# Buyurtma raqami: 1000 + id  (birinchi buyurtma #1001)
ORDER_NUMBER_BASE = 1000

# Bitta foydalanuvchida bir vaqtda kutilayotgan (pending) buyurtmalar chegarasi
MAX_PENDING_ORDERS = 5

# Aynan bir xil buyurtma shu soniya ichida ikkinchi marta qabul qilinmaydi
DUPLICATE_WINDOW_SECONDS = 60


# ---------------------------------------------------------------------
# Xatoliklar
# ---------------------------------------------------------------------
class OrderError(Exception):
    """Buyurtma logikasidagi kutilgan xatoliklarning asosiy sinfi."""


class InvalidOrderField(OrderError):
    """Bitta maydon noto'g'ri. Xabar foydalanuvchiga ko'rsatishga tayyor."""


class InvalidOrderDetails(OrderError):
    """Kerakli maydon umuman berilmagan."""


class UnknownCategory(OrderError):
    pass


class UserNotFound(OrderError):
    pass


class UserBlocked(OrderError):
    pass


class ProductNotFound(OrderError):
    pass


class PriceChanged(OrderError):
    pass


class InsufficientFunds(OrderError):
    def __init__(self, balance: float, price: float):
        super().__init__("Balans yetarli emas")
        self.balance = balance
        self.price = price


class TooManyPendingOrders(OrderError):
    pass


class DuplicateOrder(OrderError):
    pass


class OrderNotFound(OrderError):
    pass


class OrderNotPending(OrderError):
    """Buyurtma 'pending' holatida emas (allaqachon ko'rib chiqilgan)."""


class OrderNotApproved(OrderError):
    """Buyurtma 'approved' holatida emas (bajarilgan/rad etilgan/qaytarilgan)."""


# ---------------------------------------------------------------------
# Maydon tekshiruvlari
# ---------------------------------------------------------------------
def _validate_nickname(value: str) -> str:
    cleaned = " ".join(value.split())
    if not 1 <= len(cleaned) <= 32:
        raise InvalidOrderField("Nickname 1 dan 32 tagacha belgidan iborat bo'lishi kerak.")
    if any(unicodedata.category(ch) == "Cc" for ch in cleaned):
        raise InvalidOrderField("Nickname'da noto'g'ri belgilar bor.")
    return cleaned


def _digits_validator(what: str, min_len: int, max_len: int) -> Callable[[str], str]:
    def validate(value: str) -> str:
        cleaned = re.sub(r"\s", "", value)
        if not re.fullmatch(r"[0-9]+", cleaned) or not (min_len <= len(cleaned) <= max_len):
            raise InvalidOrderField(
                f"{what} faqat raqamlardan iborat bo'lishi kerak ({min_len}-{max_len} ta raqam)."
            )
        return cleaned

    return validate


_USERNAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{4,31}")


def _validate_telegram_username(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(
        r"^(?:https?://)?(?:www\.)?(?:t|telegram)\.me/", "", cleaned, flags=re.IGNORECASE
    )
    cleaned = cleaned.lstrip("@").rstrip("/")
    if not _USERNAME_RE.fullmatch(cleaned):
        raise InvalidOrderField(
            "Telegram username noto'g'ri. U 5-32 belgidan iborat, lotin harfi bilan "
            "boshlanadi va faqat lotin harflari, raqamlar hamda _ dan iborat bo'ladi."
        )
    return "@" + cleaned


# ---------------------------------------------------------------------
# Mahsulot turlari va ulardan so'raladigan ma'lumotlar
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class OrderField:
    key: str  # orders jadvalidagi ustun: nickname, game_id, zone_id, target_username
    emoji: str
    label: str  # tasdiqlash ekranida: "PUBG ID"
    admin_label: str  # admin xabarida: "O'yinchi Nickname"
    prompt: str  # foydalanuvchiga savol
    example: str
    validator: Callable[[str], str]


@dataclass(frozen=True)
class CategoryInfo:
    slug: str
    emoji: str
    title: str
    kind_emoji: str
    kind_label: str  # "O'yin" yoki "Xizmat"
    fields: Tuple[OrderField, ...]


def _nickname_field(game: str) -> OrderField:
    return OrderField(
        key="nickname",
        emoji="👤",
        label="Nickname",
        admin_label="O'yinchi Nickname",
        prompt=f"{game} nickname'ingizni kiriting:",
        example="LUCIFER",
        validator=_validate_nickname,
    )


def _username_field(prompt: str) -> OrderField:
    return OrderField(
        key="target_username",
        emoji="👤",
        label="Telegram username",
        admin_label="Telegram username",
        prompt=prompt,
        example="@username",
        validator=_validate_telegram_username,
    )


CATEGORIES: Dict[str, CategoryInfo] = {
    "pubg": CategoryInfo(
        slug="pubg",
        emoji="🎮",
        title="PUBG Mobile",
        kind_emoji="🎮",
        kind_label="O'yin",
        fields=(
            _nickname_field("PUBG Mobile"),
            OrderField(
                key="game_id",
                emoji="🆔",
                label="PUBG ID",
                admin_label="PUBG ID",
                prompt="PUBG ID raqamingizni kiriting:",
                example="5123456789",
                validator=_digits_validator("PUBG ID", 6, 14),
            ),
        ),
    ),
    "mobile_legends": CategoryInfo(
        slug="mobile_legends",
        emoji="💎",
        title="Mobile Legends",
        kind_emoji="🎮",
        kind_label="O'yin",
        fields=(
            _nickname_field("Mobile Legends"),
            OrderField(
                key="game_id",
                emoji="🆔",
                label="User ID",
                admin_label="User ID",
                prompt="Mobile Legends User ID raqamingizni kiriting:",
                example="123456789",
                validator=_digits_validator("User ID", 5, 12),
            ),
            OrderField(
                key="zone_id",
                emoji="🌐",
                label="Zone ID",
                admin_label="Zone ID",
                prompt="Zone ID ni kiriting (User ID yonidagi qavs ichidagi raqam):",
                example="2001",
                validator=_digits_validator("Zone ID", 3, 6),
            ),
        ),
    ),
    "free_fire": CategoryInfo(
        slug="free_fire",
        emoji="🔥",
        title="Free Fire",
        kind_emoji="🎮",
        kind_label="O'yin",
        fields=(
            _nickname_field("Free Fire"),
            OrderField(
                key="game_id",
                emoji="🆔",
                label="Player ID",
                admin_label="Player ID",
                prompt="Free Fire Player ID raqamingizni kiriting:",
                example="1234567890",
                validator=_digits_validator("Player ID", 6, 14),
            ),
        ),
    ),
    "telegram_stars": CategoryInfo(
        slug="telegram_stars",
        emoji="⭐",
        title="Telegram Stars",
        kind_emoji="📲",
        kind_label="Xizmat",
        fields=(_username_field("Stars yuborilishi kerak bo'lgan Telegram username'ni kiriting:"),),
    ),
    "telegram_premium": CategoryInfo(
        slug="telegram_premium",
        emoji="💎",
        title="Telegram Premium",
        kind_emoji="📲",
        kind_label="Xizmat",
        fields=(_username_field("Premium beriladigan Telegram username'ni kiriting:"),),
    ),
}


def get_category(slug: str) -> CategoryInfo:
    info = CATEGORIES.get(slug)
    if info is None:
        raise UnknownCategory(slug)
    return info


def validate_details(category: CategoryInfo, details: dict) -> Dict[str, str]:
    """Barcha kerakli maydonlarni tekshiradi va tozalangan qiymatlarni qaytaradi."""
    clean: Dict[str, str] = {}
    for field in category.fields:
        raw = details.get(field.key)
        if not isinstance(raw, str) or not raw.strip():
            raise InvalidOrderDetails(f"'{field.label}' kiritilmagan")
        clean[field.key] = field.validator(raw)
    return clean


# ---------------------------------------------------------------------
# Natija turlari
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class OrderResult:
    order_id: int
    order_number: str
    telegram_id: int
    category: str
    product_name: str
    price: float
    status: str
    payment_status: str
    nickname: Optional[str] = None
    game_id: Optional[str] = None
    zone_id: Optional[str] = None
    target_username: Optional[str] = None


@dataclass(frozen=True)
class OrderSummary:
    order_number: str
    category: str
    product_name: str
    price: float
    status: str
    created_at: Optional[datetime]


# ---------------------------------------------------------------------
# Buyurtma yaratish
# ---------------------------------------------------------------------
def create_order(
    db,
    telegram_id: int,
    product_id: int,
    details: dict,
    expected_price: Optional[float] = None,
) -> OrderResult:
    """
    Yangi 'pending' buyurtma yaratadi. Balansdan pul YECHILMAYDI.

    expected_price berilsa va mahsulot narxi shundan farq qilsa, PriceChanged
    ko'tariladi (foydalanuvchi ko'rgan narx bilan haqiqiy narx mos kelishi uchun).
    """
    try:
        # Yozish qulfini olish (yuqoridagi izohga qarang) va foydalanuvchi borligini tekshirish
        locked = db.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(updated_at=User.updated_at)
            .execution_options(synchronize_session=False)
        )
        if locked.rowcount != 1:
            raise UserNotFound()

        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user.is_blocked:
            raise UserBlocked()

        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.active == True)  # noqa: E712
            .first()
        )
        if product is None:
            raise ProductNotFound()

        category = get_category(product.category)
        clean = validate_details(category, details)

        if expected_price is not None and abs(product.price - expected_price) > 0.001:
            raise PriceChanged()

        if user.balance < product.price:
            raise InsufficientFunds(user.balance, product.price)

        since = datetime.utcnow() - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
        duplicate = (
            db.query(Order.id)
            .filter(
                Order.telegram_id == telegram_id,
                Order.product_id == product.id,
                Order.status == "pending",
                Order.created_at >= since,
                Order.nickname == clean.get("nickname"),
                Order.game_id == clean.get("game_id"),
                Order.zone_id == clean.get("zone_id"),
                Order.target_username == clean.get("target_username"),
            )
            .first()
        )
        if duplicate is not None:
            raise DuplicateOrder()

        pending_count = (
            db.query(Order)
            .filter(Order.telegram_id == telegram_id, Order.status == "pending")
            .count()
        )
        if pending_count >= MAX_PENDING_ORDERS:
            raise TooManyPendingOrders()

        order = Order(
            order_number=uuid.uuid4().hex,  # vaqtincha, quyida haqiqiysi qo'yiladi
            telegram_id=telegram_id,
            product_id=product.id,
            category=product.category,
            product_name=product.name,
            price=product.price,  # narx buyurtma paytida "muzlatiladi"
            nickname=clean.get("nickname"),
            game_id=clean.get("game_id"),
            zone_id=clean.get("zone_id"),
            target_username=clean.get("target_username"),
            status="pending",
            payment_status="unpaid",
        )
        db.add(order)
        db.flush()
        order.order_number = str(ORDER_NUMBER_BASE + order.id)

        result = OrderResult(
            order_id=order.id,
            order_number=order.order_number,
            telegram_id=telegram_id,
            category=order.category,
            product_name=order.product_name,
            price=order.price,
            status=order.status,
            payment_status=order.payment_status,
            nickname=order.nickname,
            game_id=order.game_id,
            zone_id=order.zone_id,
            target_username=order.target_username,
        )
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def list_user_orders(db, telegram_id: int, limit: int = 10) -> List[OrderSummary]:
    """Foydalanuvchining oxirgi buyurtmalari (yangisi birinchi)."""
    rows = (
        db.query(Order)
        .filter(Order.telegram_id == telegram_id)
        .order_by(Order.id.desc())
        .limit(limit)
        .all()
    )
    return [
        OrderSummary(
            order_number=o.order_number,
            category=o.category,
            product_name=o.product_name,
            price=o.price,
            status=o.status,
            created_at=o.created_at,
        )
        for o in rows
    ]


# ---------------------------------------------------------------------
# Admin amallari (4-bosqich): TASDIQLASH / BAJARILDI / RAD ETISH / QAYTARISH
#
# MUHIM ARXITEKTURA QARORI: bu funksiyalar faqat buyurtmaning HOLATINI
# atomik ravishda o'zgartiradi va COMMIT QILMAYDI. Balansni o'zgartirish
# (tasdiqlashda - yechish, qaytarishda - qo'shish) chaqiruvchi tomonidan
# backend/services/balance_service.py dagi tayyor va sinovdan o'tgan
# `apply_balance_change()` funksiyasi bilan, BIR XIL tranzaksiyada
# (bitta db.commit()) amalga oshiriladi. Shu orqali "buyurtma holati
# o'zgardi, lekin balans o'zgarmadi" (yoki aksincha) degan xavfli holat
# HECH QACHON yuzaga kelmaydi - ikkalasi yoki birga bajariladi, yoki
# birortasi ham bajarilmaydi.
#
# Bu funksiyalar order_service.py ichida balance_service ni IMPORT
# QILMAYDI (ikkala servis bir-biridan mustaqil, faqat "models" ga bog'liq) -
# ularni birlashtirish chaqiruvchining (bot/handlers/admin.py) vazifasi.
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class OrderActionResult:
    """
    Admin amali (tasdiqlash/bajarish/rad etish/qaytarish) natijasi.
    OrderResult'dan farqi: bu buyurtma bazadan QAYTA o'qilganda hosil
    bo'ladi (create_order paytida emas), shuning uchun hamma maydonlarni
    (jumladan nickname/game_id kabi tafsilotlarni) o'z ichiga oladi - bu
    admin xabarini keyinchalik yangilashda kerak bo'ladi.
    """

    order_id: int
    order_number: str
    telegram_id: int
    category: str
    product_name: str
    price: float
    status: str
    payment_status: str
    nickname: Optional[str] = None
    game_id: Optional[str] = None
    zone_id: Optional[str] = None
    target_username: Optional[str] = None


def _claim_status(db, order_id: int, from_status: str, to_status: str, extra_values: Optional[dict] = None) -> int:
    values = {"status": to_status, "updated_at": datetime.utcnow()}
    if extra_values:
        values.update(extra_values)
    result = db.execute(
        update(Order)
        .where(Order.id == order_id, Order.status == from_status)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount


def get_order_result(db, order_id: int) -> OrderActionResult:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise OrderNotFound()
    return OrderActionResult(
        order_id=order.id,
        order_number=order.order_number,
        telegram_id=order.telegram_id,
        category=order.category,
        product_name=order.product_name,
        price=order.price,
        status=order.status,
        payment_status=order.payment_status,
        nickname=order.nickname,
        game_id=order.game_id,
        zone_id=order.zone_id,
        target_username=order.target_username,
    )


def claim_order_approval(db, order_id: int) -> OrderActionResult:
    """
    Buyurtmani 'pending' -> 'approved' qiladi (atomik, ikki marta
    tasdiqlashdan himoyalangan). COMMIT QILMAYDI (yuqoridagi izohga qarang).
    """
    changed = _claim_status(db, order_id, "pending", "approved", {"payment_status": "paid"})
    if changed != 1:
        raise OrderNotFound() if _order_missing(db, order_id) else OrderNotPending()
    db.flush()
    return get_order_result(db, order_id)


def claim_order_rejection(db, order_id: int, note: Optional[str] = None) -> OrderActionResult:
    """Buyurtmani 'pending' -> 'rejected' qiladi (atomik). Balansga tegmaydi."""
    extra = {"admin_note": note} if note else None
    changed = _claim_status(db, order_id, "pending", "rejected", extra)
    if changed != 1:
        raise OrderNotFound() if _order_missing(db, order_id) else OrderNotPending()
    db.flush()
    return get_order_result(db, order_id)


def claim_order_completion(db, order_id: int) -> OrderActionResult:
    """Buyurtmani 'approved' -> 'completed' qiladi (atomik). Balansga tegmaydi."""
    changed = _claim_status(db, order_id, "approved", "completed", {"completed_at": datetime.utcnow()})
    if changed != 1:
        raise OrderNotFound() if _order_missing(db, order_id) else OrderNotApproved()
    db.flush()
    return get_order_result(db, order_id)


def claim_order_refund(db, order_id: int) -> OrderActionResult:
    """
    Buyurtmani 'approved' -> 'refunded' qiladi (atomik). COMMIT QILMAYDI -
    chaqiruvchi shu bilan birga balansga pulni qaytarishi kerak.
    """
    changed = _claim_status(db, order_id, "approved", "refunded")
    if changed != 1:
        raise OrderNotFound() if _order_missing(db, order_id) else OrderNotApproved()
    db.flush()
    return get_order_result(db, order_id)


def _order_missing(db, order_id: int) -> bool:
    return db.query(Order.id).filter(Order.id == order_id).first() is None
