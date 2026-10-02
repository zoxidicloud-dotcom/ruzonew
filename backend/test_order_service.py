"""
Buyurtma servisini sinash. Haqiqiy gaming_shop.db ga TEGMAYDI - vaqtinchalik
alohida bazada ishlaydi.

Ishga tushirish (backend/ papkasi ichida turib):
    python test_order_service.py
"""

import os
import shutil
import sys
import tempfile
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import Order, Product, User
from services import order_service as os_

TMP_DIR = tempfile.mkdtemp(prefix="gaming_shop_order_test_")
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
    s.add(User(telegram_id=telegram_id, username=f"u{telegram_id}", balance=balance,
                referral_code=f"REF{telegram_id}", is_blocked=blocked))
    s.commit()
    s.close()


def new_product(category, price, active=True):
    s = Session()
    p = Product(category=category, name=f"{category}-item", amount="x", price=price,
                currency="UZS", active=active, sort_order=1)
    s.add(p)
    s.commit()
    s.refresh(p)
    pid = p.id
    s.close()
    return pid


def balance_of(telegram_id):
    s = Session()
    try:
        return s.query(User.balance).filter(User.telegram_id == telegram_id).scalar()
    finally:
        s.close()


def order_count(telegram_id):
    s = Session()
    try:
        return s.query(Order).filter(Order.telegram_id == telegram_id).count()
    finally:
        s.close()


def raises(exc_type, func):
    s = Session()
    try:
        func(s)
        return False
    except exc_type:
        return True
    except Exception as exc:
        print("   kutilmagan xato:", type(exc).__name__, exc)
        return False
    finally:
        s.close()


try:
    # 1) Validatorlar
    check("nickname bo'shini rad etadi",
          raises(os_.InvalidOrderField, lambda db: os_.get_category("pubg").fields[0].validator("   ")))
    check("PUBG ID harflarni rad etadi",
          raises(os_.InvalidOrderField, lambda db: os_.get_category("pubg").fields[1].validator("abc123")))
    check("PUBG ID juda qisqa raqamni rad etadi",
          raises(os_.InvalidOrderField, lambda db: os_.get_category("pubg").fields[1].validator("12")))
    ml = os_.get_category("mobile_legends")
    check("Mobile Legends 3 ta maydon so'raydi", len(ml.fields) == 3)
    stars_field = os_.get_category("telegram_stars").fields[0]
    check("username @ qo'shiladi", stars_field.validator("username12345") == "@username12345")
    check("username @ bilan ham ishlaydi", stars_field.validator("@Username_1") == "@Username_1")
    check("username havola bilan ham ishlaydi", stars_field.validator("t.me/username12345") == "@username12345")
    check("username juda qisqa bo'lsa rad etiladi",
          raises(os_.InvalidOrderField, lambda db: stars_field.validator("abc")))
    check("noma'lum kategoriya: UnknownCategory",
          raises(os_.UnknownCategory, lambda db: os_.get_category("unknown")))

    # 2) Oddiy muvaffaqiyatli buyurtma (PUBG)
    new_user(100, balance=100000)
    pid_pubg = new_product("pubg", 12000)
    s = Session()
    res = os_.create_order(s, 100, pid_pubg, {"nickname": "LUCIFER", "game_id": "5123456789"})
    s.close()
    check("buyurtma yaratildi (pending)", res.status == "pending")
    check("buyurtma raqami #1001", res.order_number == "1001")
    check("narx to'g'ri saqlandi", res.price == 12000)
    check("buyurtma yaratilganda balans YECHILMAYDI", balance_of(100) == 100000)

    # 3) Mobile Legends - barcha maydonlar
    pid_ml = new_product("mobile_legends", 15000)
    s = Session()
    res_ml = os_.create_order(
        s, 100, pid_ml,
        {"nickname": "Player1", "game_id": "123456789", "zone_id": "2001"},
    )
    s.close()
    check("Mobile Legends buyurtma OK", res_ml.zone_id == "2001" and res_ml.status == "pending")

    # 4) Kerakli maydon yo'q
    check(
        "maydon yetishmasa: InvalidOrderDetails",
        raises(os_.InvalidOrderDetails, lambda db: os_.create_order(db, 100, pid_pubg, {"nickname": "X"})),
    )

    # 5) Narx o'zgargan bo'lsa
    check(
        "narx o'zgargan bo'lsa: PriceChanged",
        raises(
            os_.PriceChanged,
            lambda db: os_.create_order(
                db, 100, pid_pubg, {"nickname": "Y", "game_id": "5123456780"}, expected_price=999
            ),
        ),
    )

    # 6) Balans yetarli emas
    new_user(200, balance=5000)
    check(
        "balans yetarli emas: InsufficientFunds",
        raises(os_.InsufficientFunds, lambda db: os_.create_order(db, 200, pid_pubg, {"nickname": "Z", "game_id": "5123456781"})),
    )
    check("balans yetarli emas: buyurtma yaratilmadi", order_count(200) == 0)

    # 7) Bloklangan foydalanuvchi
    new_user(300, balance=100000, blocked=True)
    check(
        "bloklangan: UserBlocked",
        raises(os_.UserBlocked, lambda db: os_.create_order(db, 300, pid_pubg, {"nickname": "B", "game_id": "5123456782"})),
    )

    # 8) Mavjud bo'lmagan/nofaol mahsulot
    check(
        "mavjud bo'lmagan foydalanuvchi: UserNotFound",
        raises(os_.UserNotFound, lambda db: os_.create_order(db, 999999, pid_pubg, {"nickname": "N", "game_id": "5123456783"})),
    )
    pid_inactive = new_product("pubg", 12000, active=False)
    check(
        "nofaol mahsulot: ProductNotFound",
        raises(os_.ProductNotFound, lambda db: os_.create_order(db, 100, pid_inactive, {"nickname": "N", "game_id": "5123456784"})),
    )

    # 9) Dublikat (bir xil ma'lumot bilan darhol qayta yuborish)
    new_user(400, balance=100000)
    details = {"nickname": "Dup", "game_id": "5123456785"}
    s = Session()
    os_.create_order(s, 400, pid_pubg, details)
    s.close()
    check(
        "aynan bir xil buyurtma darhol qayta yuborilsa: DuplicateOrder",
        raises(os_.DuplicateOrder, lambda db: os_.create_order(db, 400, pid_pubg, details)),
    )
    check("dublikatdan keyin ham faqat 1 ta buyurtma bor", order_count(400) == 1)

    # 10) Pending limiti
    new_user(500, balance=10_000_000)
    for i in range(os_.MAX_PENDING_ORDERS):
        s = Session()
        os_.create_order(s, 500, pid_pubg, {"nickname": f"P{i}", "game_id": f"512345000{i}"})
        s.close()
    check(
        f"{os_.MAX_PENDING_ORDERS} tadan keyin: TooManyPendingOrders",
        raises(os_.TooManyPendingOrders, lambda db: os_.create_order(db, 500, pid_pubg, {"nickname": "Extra", "game_id": "5123459999"})),
    )

    # 11) Buyurtmalar tarixi
    orders_list = None
    s = Session()
    orders_list = os_.list_user_orders(s, 500, limit=3)
    s.close()
    check("list_user_orders limit ishlaydi", len(orders_list) == 3)
    check("list_user_orders eng yangisi birinchi", orders_list[0].order_number == "1008")

    # 12) RACE CONDITION: 8 ta parallel buyurtma, balans faqat 1 tasiga yetadi
    new_user(600, balance=12000)  # faqat 1 ta 12000 so'mlik mahsulotga yetadi
    outcomes = []
    lock = threading.Lock()

    def worker(i):
        session = Session()
        try:
            os_.create_order(session, 600, pid_pubg, {"nickname": f"Race{i}", "game_id": f"599900000{i}"})
            outcome = "ok"
        except os_.InsufficientFunds:
            outcome = "insufficient"
        except Exception as exc:
            outcome = f"error:{type(exc).__name__}:{exc}"
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    print("   parallel natijalar:", outcomes)
    check("parallel: buyurtma yaratish balansni yechmagani uchun barchasi o'tishi mumkin",
          outcomes.count("ok") == 8)
    check("parallel: balans hali ham 12000 (buyurtma yaratishda yechilmaydi)", balance_of(600) == 12000)
    check("parallel: 8 ta buyurtma yaratildi", order_count(600) == 8)

    # 13) ADMIN AMALLARI: tasdiqlash -> bajarish
    new_user(700, balance=50000)
    pid_admin = new_product("pubg", 12000)
    s = Session()
    order_res = os_.create_order(s, 700, pid_admin, {"nickname": "AdminTest", "game_id": "5123450001"})
    s.close()

    from services import balance_service as bs

    def approve(order_id, admin_id=999):
        session = Session()
        try:
            res = os_.claim_order_approval(session, order_id)
            bs.apply_balance_change(session, res.telegram_id, -res.price, "purchase", f"Buyurtma #{res.order_number}", reference_id=res.order_id)
            session.commit()
            return res
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    approved = approve(order_res.order_id)
    check("tasdiqlashdan keyin status='approved'", approved.status == "approved")
    check("tasdiqlashda balansdan narx yechildi", balance_of(700) == 50000 - 12000)

    check(
        "ikki marta tasdiqlash: OrderNotPending",
        raises(os_.OrderNotPending, lambda db: os_.claim_order_approval(db, order_res.order_id)),
    )
    check("ikki marta tasdiqlashda balans o'zgarmadi", balance_of(700) == 50000 - 12000)

    def complete(order_id):
        session = Session()
        try:
            res = os_.claim_order_completion(session, order_id)
            session.commit()
            return res
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    completed = complete(order_res.order_id)
    check("bajarishdan keyin status='completed'", completed.status == "completed")
    check(
        "pending bo'lmagan buyurtmani tasdiqlab bo'lmaydi (allaqachon completed)",
        raises(os_.OrderNotPending, lambda db: os_.claim_order_approval(db, order_res.order_id)),
    )
    check(
        "completed buyurtmani yana bajarib bo'lmaydi",
        raises(os_.OrderNotApproved, lambda db: os_.claim_order_completion(db, order_res.order_id)),
    )

    # 14) ADMIN AMALLARI: rad etish (balansga tegmaydi)
    s = Session()
    order_rej = os_.create_order(s, 700, pid_admin, {"nickname": "RejTest", "game_id": "5123450002"})
    s.close()

    def reject(order_id):
        session = Session()
        try:
            res = os_.claim_order_rejection(session, order_id)
            session.commit()
            return res
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    rejected = reject(order_rej.order_id)
    check("rad etishdan keyin status='rejected'", rejected.status == "rejected")
    check("rad etishda balans o'zgarmadi", balance_of(700) == 50000 - 12000)
    check(
        "rad etilgan buyurtmani tasdiqlab bo'lmaydi",
        raises(os_.OrderNotPending, lambda db: os_.claim_order_approval(db, order_rej.order_id)),
    )

    # 15) ADMIN AMALLARI: tasdiqlash -> QAYTARISH (refund)
    s = Session()
    order_ref = os_.create_order(s, 700, pid_admin, {"nickname": "RefundTest", "game_id": "5123450003"})
    s.close()
    approve(order_ref.order_id)
    check("refund testi uchun balans yechildi", balance_of(700) == 50000 - 12000 - 12000)

    def refund(order_id):
        session = Session()
        try:
            res = os_.claim_order_refund(session, order_id)
            bs.apply_balance_change(session, res.telegram_id, res.price, "refund", f"Buyurtma #{res.order_number} qaytarildi", reference_id=res.order_id)
            session.commit()
            return res
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    refunded = refund(order_ref.order_id)
    check("qaytarishdan keyin status='refunded'", refunded.status == "refunded")
    check("qaytarishda balans to'liq qaytdi", balance_of(700) == 50000 - 12000)
    check(
        "refund qilingan buyurtmani yana bajarib bo'lmaydi",
        raises(os_.OrderNotApproved, lambda db: os_.claim_order_completion(db, order_ref.order_id)),
    )
    check(
        "pending bo'lmagan buyurtmani rad etib bo'lmaydi (approved edi, endi refunded)",
        raises(os_.OrderNotPending, lambda db: os_.claim_order_rejection(db, order_ref.order_id)),
    )

    # 16) Mavjud bo'lmagan buyurtma
    check(
        "mavjud bo'lmagan buyurtma: OrderNotFound",
        raises(os_.OrderNotFound, lambda db: os_.claim_order_approval(db, 9999999)),
    )

    # 17) RACE CONDITION: 8 ta parallel tasdiqlash (bitta buyurtma)
    new_user(800, balance=100000)
    s = Session()
    order_race = os_.create_order(s, 800, pid_admin, {"nickname": "Race", "game_id": "5123450004"})
    s.close()

    outcomes = []
    lock = threading.Lock()

    def approve_worker():
        session = Session()
        try:
            res = os_.claim_order_approval(session, order_race.order_id)
            bs.apply_balance_change(session, res.telegram_id, -res.price, "purchase", "race-test", reference_id=res.order_id)
            session.commit()
            outcome = "ok"
        except os_.OrderNotPending:
            session.rollback()
            outcome = "already"
        except Exception as exc:
            session.rollback()
            outcome = f"error:{type(exc).__name__}:{exc}"
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=approve_worker) for _ in range(8)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    print("   parallel tasdiqlash natijalari:", outcomes)
    check("parallel tasdiqlash: faqat 1 ta o'tdi", outcomes.count("ok") == 1)
    check("parallel tasdiqlash: qolgan 7 tasi rad etildi", outcomes.count("already") == 7)
    check("parallel tasdiqlash: balans FAQAT BIR MARTA yechildi", balance_of(800) == 100000 - 12000)

finally:
    engine.dispose()
    shutil.rmtree(TMP_DIR, ignore_errors=True)