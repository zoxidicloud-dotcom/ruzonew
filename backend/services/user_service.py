"""
Foydalanuvchini ro'yxatdan o'tkazish / ma'lumotlarini yangilash - YAGONA
biznes-logika. Buni ilgari Telegram bot (handlers/start.py) o'zida alohida
yozgan edi; endi backend (Telegram Mini App autentifikatsiyasi, 6-bosqich)
ham xuddi shu foydalanuvchi bilan ishlashi kerak bo'lgani uchun bu yerga,
umumiy joyga ko'chirildi - ikkala joyda alohida-alohida yozilmasin.
"""

import random
import string

from models import User


def _generate_referral_code(db, length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(chars) for _ in range(length))
        if db.query(User).filter(User.referral_code == code).first() is None:
            return code


def get_or_create_user(
    db,
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    is_admin: bool = False,
) -> User:
    """
    Berilgan Telegram foydalanuvchisi uchun database'dan User qatorini
    topadi, topilmasa - yangisini yaratadi. Mavjud bo'lsa, username/ism
    o'zgargan bo'lsa yangilaydi.
    """
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if user:
        changed = False
        if user.username != username:
            user.username = username
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if is_admin and not user.is_admin:
            user.is_admin = True
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        balance=0,
        referral_code=_generate_referral_code(db),
        is_admin=is_admin,
        is_blocked=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
