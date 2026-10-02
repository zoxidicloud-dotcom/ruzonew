"""
Gaming Shop - Backend API (FastAPI).

Ishga tushirish (backend/ papkasi ichida turib):
    python -m uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from catalog import PRODUCTS
from database import Base, SessionLocal, engine
import models  # noqa: F401  - jadvallarni Base.metadata ga ro'yxatdan o'tkazish uchun kerak
from models import Product
from routers import auth, balance, orders, products, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gaming Shop API",
    description="PUBG UC, Mobile Legends Diamonds, Free Fire Diamonds, "
    "Telegram Stars va Premium sotib olish platformasi API'si.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(balance.router)
app.include_router(orders.router)


def _seed_products_if_empty() -> None:
    """Baza bo'sh bo'lsa, catalog.py dagi mahsulotlarni yozadi."""
    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            return
        for category, name, amount, price, sort_order, description in PRODUCTS:
            db.add(
                Product(
                    category=category,
                    name=name,
                    amount=amount,
                    price=price,
                    currency="UZS",
                    description=description,
                    active=True,
                    sort_order=sort_order,
                )
            )
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    _seed_products_if_empty()


@app.get("/")
def root():
    return {"status": "ok", "message": "Gaming Shop backend ishlayapti"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
