"""
Database jadvallari (SQLAlchemy modellari).

Bu yerda loyihaning YAKUNIY (barcha bosqichlar uchun) sxemasi to'liq
belgilangan. 1-bosqichda faqat User va Product jadvallari to'ldiriladi,
qolganlari keyingi bosqichlarda ishlatiladi - lekin sxemani boshidanoq
to'liq yozib qo'yish, keyinchalik jadval qo'shish/o'zgartirish
(migratsiya) muammolarining oldini oladi.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    balance = Column(Float, default=0, nullable=False)
    referral_code = Column(String(32), unique=True, index=True, nullable=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(String(64), nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(16), default="UZS", nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(32), unique=True, index=True, nullable=False)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    category = Column(String(64), nullable=False)
    product_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)

    game_id = Column(String(64), nullable=True)
    zone_id = Column(String(64), nullable=True)
    nickname = Column(String(255), nullable=True)
    target_username = Column(String(255), nullable=True)

    status = Column(String(32), default="pending", nullable=False)
    payment_status = Column(String(32), default="unpaid", nullable=False)
    admin_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)


class BalanceTopup(Base):
    __tablename__ = "balance_topups"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    receipt_file_id = Column(String(255), nullable=True)
    status = Column(String(32), default="pending", nullable=False)
    admin_message_id = Column(Integer, nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)


class BalanceTransaction(Base):
    __tablename__ = "balance_transactions"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(32), nullable=False)  # topup, purchase, refund, admin_add, admin_sub
    description = Column(String(255), nullable=True)
    reference_id = Column(Integer, nullable=True)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PromoUsage(Base):
    __tablename__ = "promo_usage"

    id = Column(Integer, primary_key=True, index=True)
    promo_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(64), nullable=False)
    target_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
