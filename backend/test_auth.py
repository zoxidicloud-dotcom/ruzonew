"""
auth.py ni sinash. Sof Python (hashlib/hmac/json) - hech qanday tashqi
kutubxona kerak emas, shuning uchun bu testni HOZIROQ, sqlalchemy
o'rnatilmagan bo'lsa ham ishga tushirish mumkin.

Ishga tushirish:
    python test_auth.py
"""

import hashlib
import hmac
import json
import sys
import time
from urllib.parse import urlencode

from auth import (
    AuthError,
    create_session_token,
    validate_init_data,
    verify_session_token,
)

BOT_TOKEN = "123456789:TEST-TOKEN-FOR-UNIT-TESTS-ONLY"
SESSION_SECRET = "test-session-secret-please-change-in-real-env"

results = []


def check(name, condition):
    print(("OK    " if condition else "XATO  ") + name)
    results.append(bool(condition))


def build_init_data(user: dict, auth_date: int, bot_token: str = BOT_TOKEN, bad_hash: bool = False) -> str:
    """Telegram yuboradigan haqiqiy initData'ga o'xshash qator yasaydi (test uchun)."""
    data = {
        "query_id": "AAEXAMPLE",
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": str(auth_date),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    correct_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    data["hash"] = "0" * 64 if bad_hash else correct_hash
    return urlencode(data)


try:
    now = int(time.time())
    user = {"id": 123456789, "username": "ali", "first_name": "Ali", "last_name": "Valiyev"}

    # 1) TO'G'RI initData - qabul qilinishi kerak
    good = build_init_data(user, now)
    parsed = validate_init_data(good, BOT_TOKEN)
    check("to'g'ri initData qabul qilindi", parsed["id"] == 123456789)
    check("username to'g'ri o'qildi", parsed["username"] == "ali")

    # 2) SOXTA hash - rad etilishi SHART (bu eng muhim test!)
    bad = build_init_data(user, now, bad_hash=True)
    try:
        validate_init_data(bad, BOT_TOKEN)
        check("SOXTA hash rad etildi", False)
    except AuthError:
        check("SOXTA hash rad etildi", True)

    # 3) Boshqa bot tokeni bilan imzolangan (masalan boshqa birovning boti)
    other_bot = build_init_data(user, now, bot_token="987654321:OTHER-BOT-TOKEN")
    try:
        validate_init_data(other_bot, BOT_TOKEN)
        check("boshqa bot tokeni bilan imzolangan initData rad etildi", False)
    except AuthError:
        check("boshqa bot tokeni bilan imzolangan initData rad etildi", True)

    # 4) O'zgartirilgan foydalanuvchi ID (hash eskiligicha qoladi -> mos kelmaydi)
    tampered = good.replace("123456789", "999999999")
    try:
        validate_init_data(tampered, BOT_TOKEN)
        check("o'zgartirilgan ma'lumot (tampering) rad etildi", False)
    except AuthError:
        check("o'zgartirilgan ma'lumot (tampering) rad etildi", True)

    # 5) Juda eski initData (25 soat oldin) - rad etilishi kerak
    old = build_init_data(user, now - 25 * 60 * 60)
    try:
        validate_init_data(old, BOT_TOKEN)
        check("25 soatlik eski initData rad etildi", False)
    except AuthError:
        check("25 soatlik eski initData rad etildi", True)

    # 6) Yaqin o'tmish (1 soat oldin) - hali ham qabul qilinishi kerak
    recent = build_init_data(user, now - 60 * 60)
    parsed2 = validate_init_data(recent, BOT_TOKEN)
    check("1 soat oldingi initData hali ham qabul qilinadi", parsed2["id"] == 123456789)

    # 7) hash umuman yo'q
    no_hash = "query_id=AAA&user=%7B%7D&auth_date=" + str(now)
    try:
        validate_init_data(no_hash, BOT_TOKEN)
        check("hash yo'q bo'lsa rad etiladi", False)
    except AuthError:
        check("hash yo'q bo'lsa rad etiladi", True)

    # 8) bo'sh initData
    try:
        validate_init_data("", BOT_TOKEN)
        check("bo'sh initData rad etiladi", False)
    except AuthError:
        check("bo'sh initData rad etiladi", True)

    # ============== SESSIYA TOKENI ==============

    # 9) Yaratilgan token darhol tekshirilganda to'g'ri ID qaytarishi kerak
    token = create_session_token(123456789, SESSION_SECRET)
    telegram_id = verify_session_token(token, SESSION_SECRET)
    check("sessiya tokeni to'g'ri ID qaytardi", telegram_id == 123456789)

    # 10) Noto'g'ri secret bilan tekshirilsa rad etilishi kerak
    try:
        verify_session_token(token, "boshqa-noto'g'ri-secret")
        check("noto'g'ri secret bilan token rad etildi", False)
    except AuthError:
        check("noto'g'ri secret bilan token rad etildi", True)

    # 11) Buzilgan (o'zgartirilgan) token rad etilishi kerak
    corrupted = token[:-4] + "abcd"
    try:
        verify_session_token(corrupted, SESSION_SECRET)
        check("buzilgan token rad etildi", False)
    except AuthError:
        check("buzilgan token rad etildi", True)

    # 12) Muddati o'tgan token (sun'iy ravishda yaratamiz)
    import base64

    expired_payload = f"123456789:{now - 100}"
    expired_sig = hmac.new(SESSION_SECRET.encode(), expired_payload.encode(), hashlib.sha256).hexdigest()
    expired_token = base64.urlsafe_b64encode(f"{expired_payload}:{expired_sig}".encode()).decode()
    try:
        verify_session_token(expired_token, SESSION_SECRET)
        check("muddati o'tgan token rad etildi", False)
    except AuthError:
        check("muddati o'tgan token rad etildi", True)

    # 13) Umuman noto'g'ri formatdagi token
    try:
        verify_session_token("bu-token-emas", SESSION_SECRET)
        check("noto'g'ri formatdagi token rad etildi", False)
    except AuthError:
        check("noto'g'ri formatdagi token rad etildi", True)

finally:
    pass

print()
if all(results):
    print(f"HAMMA TESTLAR O'TDI ({len(results)} ta)")
    sys.exit(0)
print(f"XATO: {results.count(False)} ta test o'tmadi (jami {len(results)} ta)")
sys.exit(1)
