"""
Bot uchun database ulanishi va backend kodini qayta ishlatish.

MUHIM ARXITEKTURA QARORI:
Bot o'zining alohida jadval klasslarini va biznes-logikasini yozmaydi.
Ushbu fayl to'g'ridan-to'g'ri quyidagi backend fayllarini yuklab ishlatadi:

  - backend/database.py          (engine, SessionLocal, Base)
  - backend/models.py            (jadval ta'riflari)
  - backend/services/balance_service.py  (balans biznes-logikasi)
  - backend/services/order_service.py    (buyurtma biznes-logikasi)

Natijada bot va backend:
  - ANIQ BIR XIL "gaming_shop.db" fayliga ulanadi,
  - jadval sxemasi FAQAT BITTA JOYDA yoziladi,
  - balans logikasi (qo'shish, tasdiqlash, ...) FAQAT BITTA JOYDA yoziladi.

Texnik izoh: oddiy "import database" ishlatib bo'lmaydi, chunki bu fayl
ham "database" deb nomlangan (nom to'qnashuvi bo'ladi). Shuning uchun
backend fayllari Python'ning "importlib" mexanizmi orqali maxsus
nomlar ostida yuklanadi.
"""

import importlib.util
import os
import sys

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BOT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")


def _load_backend_module(unique_name: str, relative_path: str):
    file_path = os.path.join(BACKEND_DIR, *relative_path.split("/"))
    if not os.path.isfile(file_path):
        raise RuntimeError(
            f"'{file_path}' topilmadi. 'backend' papkasi joyida ekanligini tekshiring."
        )
    spec = importlib.util.spec_from_file_location(unique_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


# 1) backend/database.py (engine, SessionLocal, Base, get_db)
_backend_database = _load_backend_module("_backend_database", "database.py")

engine = _backend_database.engine
SessionLocal = _backend_database.SessionLocal
Base = _backend_database.Base
get_db = _backend_database.get_db

# 2) backend/models.py ("from database import Base" qatori shu faylga
#    (sys.modules["database"]) murojaat qiladi - Base yuqorida biriktirilgan)
_backend_models = _load_backend_module("_backend_models", "models.py")

User = _backend_models.User
Product = _backend_models.Product
Order = _backend_models.Order
BalanceTopup = _backend_models.BalanceTopup
BalanceTransaction = _backend_models.BalanceTransaction
PromoCode = _backend_models.PromoCode
PromoUsage = _backend_models.PromoUsage
Referral = _backend_models.Referral
AdminLog = _backend_models.AdminLog

# 3) backend/services/*.py fayllari "from models import ..." deb yozilgan.
#    Shu nom ("models") ostida yuqorida yuklangan modelni ro'yxatdan o'tkazamiz.
sys.modules["models"] = _backend_models

balance_service = _load_backend_module(
    "_backend_balance_service", "services/balance_service.py"
)
order_service = _load_backend_module(
    "_backend_order_service", "services/order_service.py"
)
user_service = _load_backend_module(
    "_backend_user_service", "services/user_service.py"
)
