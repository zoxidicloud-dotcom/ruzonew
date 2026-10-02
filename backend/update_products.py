"""
Mahsulotlarni catalog.py dagi yangi ro'yxat bilan almashtirish.

Ishga tushirish (backend/ papkasi ichida turib):
    python update_products.py

Xavfsizlik: agar bazada allaqachon buyurtmalar bo'lsa, eski mahsulotlar
o'chirilmaydi (buyurtmalar ularga bog'langan) - ular faqat "nofaol"
qilinadi va yangilari qo'shiladi.
"""

from database import Base, SessionLocal, engine
from models import Order, Product
from catalog import PRODUCTS

Base.metadata.create_all(bind=engine)


def main() -> None:
    db = SessionLocal()
    try:
        has_orders = db.query(Order).count() > 0

        if has_orders:
            db.query(Product).update({Product.active: False})
            mode = "eski mahsulotlar nofaol qilindi"
        else:
            db.query(Product).delete()
            mode = "eski mahsulotlar o'chirildi"

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
        print(f"OK: {mode}, {len(PRODUCTS)} ta yangi mahsulot qo'shildi.")
    except Exception as exc:
        db.rollback()
        print(f"XATO: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
