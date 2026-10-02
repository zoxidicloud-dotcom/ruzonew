"""
Balans servisini sinash. Haqiqiy gaming_shop.db ga TEGMAYDI:
vaqtinchalik papkada alohida test bazasi yaratadi va oxirida o'chiradi.

Ishga tushirish (backend/ papkasi ichida turib):
    python test_balance_service.py

Kutilgan natija: barcha qatorlar "OK" bilan boshlanadi va oxirida
"HAMMA TESTLAR O'TDI" yoziladi.
"""

import os
import shutil
import sys
import tempfile
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import BalanceTransaction, User
from services import balance_service as bs

TMP_DIR = tempfile.mkdtemp(prefix="gaming_shop_test_")
engine = create_engine(
    f"sqlite:///{os.path.join(TMP_DIR, 'test.db')}",
    connect_args={"check_same_thread": False, "timeout": 30},
)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

results = []


def check(name, condition):
    print(("OK    " if condition else "XATO  ") + name)
    results.append(bool(condition))


def new_user(telegram_id, balance=0, blocked=False):
    s = Session()
    s.add(
        User(
            telegram_id=telegram_id,
            username=f"user{telegram_id}",
            balance=balance,
            referral_code=f"REF{telegram_id}",
            is_blocked=blocked,
        )
    )
    s.commit()
    s.close()


def new_topup(telegram_id, amount):
    s = Session()
    try:
        return bs.create_topup_request(s, telegram_id, amount, "file_id_test").topup_id
    finally:
        s.close()


def balance_of(telegram_id):
    s = Session()
    try:
        return s.query(User.balance).filter(User.telegram_id == telegram_id).scalar()
    finally:
        s.close()


def tx_count(telegram_id):
    s = Session()
    try:
        return (
            s.query(BalanceTransaction)
            .filter(BalanceTransaction.telegram_id == telegram_id)
            .count()
        )
    finally:
        s.close()


def raises(exc_type, func):
    s = Session()
    try:
        func(s)
        return False
    except exc_type:
        return True
    except Exception as exc:  # boshqa xato - test muvaffaqiyatsiz
        print("   kutilmagan xato:", type(exc).__name__, exc)
        return False
    finally:
        s.close()


try:
    # 1) Oddiy tasdiqlash
    new_user(100)
    t1 = new_topup(100, 50000)
    s = Session()
    res = bs.approve_topup(s, t1, 999)
    s.close()
    check("tasdiqlash: balans 50000 bo'ldi", balance_of(100) == 50000)
    check("tasdiqlash: natijada balance_after=50000", res.balance_after == 50000)
    check("tasdiqlash: 1 ta tranzaksiya yozildi", tx_count(100) == 1)

    # 2) Ikkinchi marta tasdiqlash
    check(
        "ikki marta tasdiqlash rad etildi",
        raises(bs.TopupAlreadyProcessed, lambda db: bs.approve_topup(db, t1, 999)),
    )
    check("ikki marta tasdiqlash: balans o'zgarmadi", balance_of(100) == 50000)
    check("ikki marta tasdiqlash: tranzaksiya ko'paymadi", tx_count(100) == 1)

    # 3) Rad etish
    t2 = new_topup(100, 20000)
    s = Session()
    bs.reject_topup(s, t2, 999)
    s.close()
    check("rad etish: balans o'zgarmadi", balance_of(100) == 50000)
    check(
        "rad etilgan so'rovni tasdiqlab bo'lmaydi",
        raises(bs.TopupAlreadyProcessed, lambda db: bs.approve_topup(db, t2, 999)),
    )
    check("rad etilgandan keyin ham balans o'zgarmadi", balance_of(100) == 50000)

    # 4) Mavjud bo'lmagan so'rov
    check(
        "mavjud bo'lmagan so'rov: TopupNotFound",
        raises(bs.TopupNotFound, lambda db: bs.approve_topup(db, 99999, 999)),
    )

    # 5) RACE CONDITION: 8 ta parallel tasdiqlash
    new_user(200)
    t3 = new_topup(200, 10000)
    outcomes = []
    lock = threading.Lock()

    def worker():
        session = Session()
        try:
            bs.approve_topup(session, t3, 999)
            outcome = "ok"
        except bs.TopupAlreadyProcessed:
            outcome = "already"
        except Exception as exc:
            outcome = f"error:{type(exc).__name__}:{exc}"
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    print("   parallel natijalar:", outcomes)
    check("parallel: aynan 1 ta tasdiqlash o'tdi", outcomes.count("ok") == 1)
    check("parallel: qolgan 7 tasi rad etildi", outcomes.count("already") == 7)
    check("parallel: balans FAQAT BIR MARTA qo'shildi", balance_of(200) == 10000)
    check("parallel: faqat 1 ta tranzaksiya", tx_count(200) == 1)

    # 6) Balans yetarli bo'lmasa
    s = Session()
    try:
        bs.apply_balance_change(s, 200, -999999, "purchase", "test")
        s.commit()
        insufficient = False
    except bs.InsufficientBalance:
        s.rollback()
        insufficient = True
    finally:
        s.close()
    check("balans yetarli emas: InsufficientBalance", insufficient)
    check("balans yetarli emas: balans o'zgarmadi", balance_of(200) == 10000)

    s = Session()
    bs.apply_balance_change(s, 200, -4000, "purchase", "test")
    s.commit()
    s.close()
    check("balansdan ayirish ishladi (10000-4000)", balance_of(200) == 6000)

    # 7) Tekshiruvlar
    check(
        "summa juda kichik: InvalidAmount",
        raises(bs.InvalidAmount, lambda db: bs.create_topup_request(db, 200, 10, "f")),
    )
    check(
        "summa juda katta: InvalidAmount",
        raises(bs.InvalidAmount, lambda db: bs.create_topup_request(db, 200, 10**10, "f")),
    )
    new_user(300, blocked=True)
    check(
        "bloklangan foydalanuvchi: UserBlocked",
        raises(bs.UserBlocked, lambda db: bs.create_topup_request(db, 300, 5000, "f")),
    )
    check(
        "noma'lum foydalanuvchi: UserNotFound",
        raises(bs.UserNotFound, lambda db: bs.create_topup_request(db, 777, 5000, "f")),
    )
    new_user(400)
    for _ in range(bs.MAX_PENDING_TOPUPS):
        new_topup(400, 5000)
    check(
        "pending limitidan oshganda: TooManyPendingTopups",
        raises(bs.TooManyPendingTopups, lambda db: bs.create_topup_request(db, 400, 5000, "f")),
    )
finally:
    engine.dispose()
    shutil.rmtree(TMP_DIR, ignore_errors=True)

print()
if all(results):
    print(f"HAMMA TESTLAR O'TDI ({len(results)} ta)")
    sys.exit(0)
print(f"XATO: {results.count(False)} ta test o'tmadi (jami {len(results)} ta)")
sys.exit(1)
