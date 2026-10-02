"""
Database ulanishi (SQLAlchemy engine + session).

MUHIM: Database faylining yo'li ATAYLAB absolyut (mutlaq) yo'l sifatida
hisoblanadi (joriy ishchi papkaga - cwd'ga bog'liq emas). Sabab: agar
nisbiy yo'l ("./gaming_shop.db") ishlatilsa va backend "backend/" papkasi
ichidan, bot esa "bot/" papkasi ichidan ishga tushirilsa - ular IKKITA
ALOHIDA fayl yaratib qo'yishi mumkin edi, va bu bot bilan sayt turli xil
ma'lumotlar ko'rishiga olib kelardi. Shu xatoning oldini olish uchun
database fayli har doim loyihaning ROOT papkasida, aniq bitta joyda
saqlanadi.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# gaming_shop/backend/database.py -> gaming_shop/ (ROOT papka)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "gaming_shop.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    # SQLite uchun: bir nechta thread/so'rov bir vaqtda ulanishi uchun kerak
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Depends() bilan ishlatiladigan database session generatori."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
