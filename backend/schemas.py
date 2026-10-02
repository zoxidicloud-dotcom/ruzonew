"""
Pydantic schemas - API request/response formatlari.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    """Mahsulotni API orqali qaytarish uchun format."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    name: str
    amount: Optional[str] = None
    price: float
    currency: str
    description: Optional[str] = None
    active: bool
    sort_order: int
    created_at: datetime
