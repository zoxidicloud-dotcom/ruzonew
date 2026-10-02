"""
Mahsulotlar katalogi (yagona manba).

Narxlarni o'zgartirmoqchi bo'lsangiz, shu ro'yxatni tahrirlab,
"python update_products.py" ni ishga tushiring.
(7-bosqichda admin paneldan ham o'zgartirish mumkin bo'ladi.)

Format: (category, name, amount, narx_som, sort_order, description)
"""

PRODUCTS = [
    # ---------------- PUBG MOBILE ----------------
    ("pubg", "60 UC", "60 UC", 12000, 1, None),
    ("pubg", "325 UC", "325 UC", 58000, 2, None),
    ("pubg", "660 UC", "660 UC", 117000, 3, None),
    ("pubg", "1800 UC", "1800 UC", 281000, 4, None),
    ("pubg", "3850 UC", "3850 UC", 570000, 5, None),
    ("pubg", "5650 UC", "5650 UC", 851000, 6, None),
    ("pubg", "8100 UC", "8100 UC", 1150000, 7, None),
    # ---------------- MOBILE LEGENDS ----------------
    ("mobile_legends", "55 Diamonds", "55 Diamonds", 11890, 1, None),
    ("mobile_legends", "86 Diamonds", "86 Diamonds", 18890, 2, None),
    ("mobile_legends", "165 Diamonds", "165 Diamonds", 33890, 3, None),
    ("mobile_legends", "172 Diamonds", "172 Diamonds", 35890, 4, None),
    ("mobile_legends", "257 Diamonds", "257 Diamonds", 49590, 5, None),
    ("mobile_legends", "275 Diamonds", "275 Diamonds", 53890, 6, None),
    ("mobile_legends", "330 Diamonds", "330 Diamonds", 65890, 7, None),
    ("mobile_legends", "440 Diamonds", "440 Diamonds", 87890, 8, None),
    ("mobile_legends", "565 Diamonds", "565 Diamonds", 109890, 9, None),
    ("mobile_legends", "706 Diamonds", "706 Diamonds", 132890, 10, None),
    # ---------------- FREE FIRE ----------------
    ("free_fire", "110 Diamonds", "110 Diamonds", 12000, 1, None),
    ("free_fire", "341 Diamonds", "341 Diamonds", 35500, 2, None),
    ("free_fire", "572 Diamonds", "572 Diamonds", 57500, 3, None),
    ("free_fire", "1166 Diamonds", "1166 Diamonds", 115000, 4, None),
    ("free_fire", "2398 Diamonds", "2398 Diamonds", 222000, 5, None),
    ("free_fire", "6160 Diamonds", "6160 Diamonds", 570000, 6, None),
    # ---------------- TELEGRAM STARS ----------------
    ("telegram_stars", "50 Stars", "50 Stars", 12000, 1, None),
    ("telegram_stars", "100 Stars", "100 Stars", 22000, 2, None),
    ("telegram_stars", "250 Stars", "250 Stars", 48000, 3, None),
    ("telegram_stars", "500 Stars", "500 Stars", 105000, 4, None),
    ("telegram_stars", "1000 Stars", "1000 Stars", 210000, 5, None),
    # ---------------- TELEGRAM PREMIUM ----------------
    ("telegram_premium", "3 oy (gift)", "3 oy", 167000, 1, "Gift orqali yuboriladi"),
    ("telegram_premium", "6 oy (gift)", "6 oy", 220000, 2, "Gift orqali yuboriladi"),
    ("telegram_premium", "12 oy (gift)", "12 oy", 390000, 3, "Gift orqali yuboriladi"),
]
