"""
Joriy foydalanuvchi balansi.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_telegram_id
from models import User

router = APIRouter(prefix="/api/balance", tags=["balance"])


@router.get("")
@router.get("/")
def get_balance(
    telegram_id: int = Depends(get_current_telegram_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return {"telegram_id": telegram_id, "balance": user.balance}
