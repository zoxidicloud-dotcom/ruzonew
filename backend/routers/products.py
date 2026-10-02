"""
Mahsulotlar bilan bog'liq API endpointlari.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Product
from schemas import ProductOut

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
@router.get("/", response_model=list[ProductOut])
def list_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Barcha faol mahsulotlarni qaytaradi. ?category=pubg orqali filtrlash mumkin."""
    query = db.query(Product).filter(Product.active == True)  # noqa: E712
    if category:
        query = query.filter(Product.category == category)
    query = query.order_by(Product.category, Product.sort_order, Product.price)
    return query.all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Bitta mahsulotni ID orqali qaytaradi."""
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.active == True)  # noqa: E712
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    return product
