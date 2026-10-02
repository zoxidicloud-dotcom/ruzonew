"""
Joriy (autentifikatsiyadan o'tgan) foydalanuvchi haqida ma'lumot.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_telegram_id
from models import Order, User

router = APIRouter(prefix="/api/me", tags=["users"])


@router.get("")
@router.get("/")
def get_me(
    telegram_id: int = Depends(get_current_telegram_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    orders_count = db.query(Order).filter(Order.telegram_id == telegram_id).count()
    referrals_count = db.query(User).filter(User.referred_by == user.id).count()

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "balance": user.balance,
        "orders_count": orders_count,
        "referrals_count": referrals_count,
        "referral_code": user.referral_code,
        "created_at": user.created_at,
    }
