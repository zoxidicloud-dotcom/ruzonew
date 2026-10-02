"""
Joriy foydalanuvchining buyurtmalar tarixi. Bir xil order_service dan
foydalanadi (bot ham xuddi shundan foydalanadi) - biznes-logika ikki
marta yozilmagan.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_telegram_id
from services import order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("")
@router.get("/")
def list_orders(
    telegram_id: int = Depends(get_current_telegram_id),
    db: Session = Depends(get_db),
):
    orders = order_service.list_user_orders(db, telegram_id, limit=20)
    return [
        {
            "order_number": o.order_number,
            "category": o.category,
            "product_name": o.product_name,
            "price": o.price,
            "status": o.status,
            "created_at": o.created_at,
        }
        for o in orders
    ]
