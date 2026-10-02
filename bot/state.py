"""
Bot ichida vaqtinchalik (RAM'dagi) holatni saqlash.

Foydalanuvchi buyurtma berish jarayonida (kategoriya tanlash -> ma'lumot
kiritish -> tasdiqlash) hali bazaga yozilmagan ma'lumotlarni shu yerda
saqlaymiz. Bot bitta jarayon (process) sifatida ishlagani uchun bu yetarli;
bot qayta ishga tushirilsa, tugallanmagan jarayonlar shunchaki yo'qoladi
(foydalanuvchi qaytadan boshlashi kerak bo'ladi) - bu xavfsiz xatti-harakat.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PendingOrder:
    product_id: int
    category_slug: str
    expected_price: float
    details: dict = field(default_factory=dict)


# telegram_id -> PendingOrder
PENDING_ORDERS: Dict[int, PendingOrder] = {}


def clear_pending_order(telegram_id: int) -> None:
    PENDING_ORDERS.pop(telegram_id, None)
