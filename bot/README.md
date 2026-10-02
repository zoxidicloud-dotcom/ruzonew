# 🎮 Gaming Shop — 2-BOSQICH (1-bosqich ustiga qurilgan)

Professional Telegram + Web gaming top-up platformasi.
Bu README hozircha faqat **1-bosqich** (Backend + Database + Telegram bot +
ReplyKeyboard + Mahsulotlar + Profil + Balans ko'rish) uchun. Keyingi
bosqichlarda README kengaytiriladi.

---

## 📁 Loyiha tuzilishi (1-bosqichda yaratilgan qism)

```
gaming_shop/
├── .env.example        ← nusxa olib .env qiling
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py          FastAPI ilovasi
│   ├── config.py        .env sozlamalari
│   ├── database.py      SQLAlchemy engine/session (BITTA haqiqiy manba)
│   ├── models.py        Barcha jadval ta'riflari (BITTA haqiqiy manba)
│   ├── schemas.py        Pydantic response formatlari
│   ├── requirements.txt
│   └── routers/
│       └── products.py  GET /api/products
│
└── bot/
    ├── bot.py            Botni ishga tushiruvchi fayl
    ├── config.py         .env sozlamalari (botga kerakli qismi)
    ├── database.py       backend/database.py va models.py'ni xavfsiz
    │                     qayta ishlatadi (pastda tushuntirilgan)
    ├── keyboards.py       ReplyKeyboard menyulari
    ├── utils.py           Narxni formatlash
    ├── requirements.txt
    └── handlers/
        ├── start.py       /start, foydalanuvchini ro'yxatga olish
        ├── shop.py        Mahsulotlarni ko'rish
        ├── balance.py     Balansni ko'rish
        ├── profile.py     Profil
        └── common.py      Orqaga/Yordam/hali tayyor bo'lmagan bo'limlar
```

---

## 🧠 Muhim arxitektura qarori: bitta database, bitta sxema

Siz so'ragan talablarda ikkita narsa bor edi:
1. Bot va backend bir xil papka strukturasida, ikkalasida ham `database.py`.
2. Bot va backend **bir xil database** va **bir xil biznes-logika**dan
   foydalanishi, kod ikki marta yozilmasligi kerak.

Agar ikkalasida alohida-alohida jadval klasslari yozilsa, ular vaqt
o'tishi bilan bir-biridan farqlanib ketishi mumkin edi (masalan, kimdir
faqat bittasiga yangi ustun qo'shib, ikkinchisini unutib qo'yishi mumkin).

**Shuning uchun:** `backend/database.py` va `backend/models.py` — yagona
haqiqat manbai. `bot/database.py` esa ularni **Python `importlib`**
mexanizmi orqali to'g'ridan-to'g'ri yuklab, qayta ishlatadi (nom
to'qnashuvisiz — fayl ichida batafsil izoh bor). Bu men bu loyihada
qabul qilgan yagona "noaniq joyni sodda va ishonchli hal qilish" qarori
bo'ldi.

Bundan tashqari, **database fayli** (`gaming_shop.db`) doim loyihaning
ROOT papkasida, **absolyut yo'l** bilan hisoblanadi — bot `bot/` ichidan,
backend `backend/` ichidan ishga tushirilsa ham, ikkalasi ham AYNAN BITTA
faylga ulanadi. Shu sababli `.env`dagi `DATABASE_URL` qatori olib
tashlandi — yo'l avtomatik va xato qilib bo'lmaydigan tarzda hisoblanadi.

---

## ⚙️ 1-QADAM: Python muhitini tayyorlash (Windows + VS Code)

VS Code'da loyiha papkasini oching (`gaming_shop/`), so'ng **Terminal → New
Terminal** orqali quyidagilarni bajaring.

### Backend uchun virtual muhit

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Bot uchun virtual muhit (alohida terminalda)

```powershell
cd bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> 💡 Ikkita alohida virtual muhit ishlatish tavsiya etiladi, chunki
> backend va bot alohida jarayon (process) sifatida ishlaydi.

---

## 🔑 2-QADAM: `.env` faylini sozlash

Loyihaning **ROOT** papkasida (`gaming_shop/` ichida, `backend/` yoki
`bot/` ichida EMAS):

```powershell
copy .env.example .env
```

`.env` faylini oching va kamida quyidagini to'ldiring:

```
BOT_TOKEN=<@BotFather bergan tokeningiz>
```

### BOT_TOKEN qanday olinadi:
1. Telegram'da **@BotFather** ga yozing.
2. `/newbot` buyrug'ini yuboring.
3. Bot uchun nom va username bering (username `bot` bilan tugashi kerak,
   masalan `MyGamingShop_bot`).
4. BotFather sizga token beradi — shu tokenni `.env` faylidagi
   `BOT_TOKEN=` qatoriga qo'ying.

### ADMIN_TELEGRAM_IDS qanday olinadi (2-bosqichdan kerak bo'ladi, lekin hozirdan to'ldirib qo'yishingiz mumkin):
1. Telegram'da **@userinfobot** ga yozing.
2. U sizga ID raqamingizni beradi.
3. Bir nechta admin bo'lsa, vergul bilan ajrating: `111111111,222222222`

`PAYMENT_CARD_NUMBER`, `ADMIN_CHANNEL_ID` — bular 2-bosqichda kerak
bo'ladi, hozircha bo'sh qoldirsangiz ham bo'ladi.

---

## ▶️ 3-QADAM: Backend'ni ishga tushirish

```powershell
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

**Kutilgan natija** — terminalda shunga o'xshash chiqishi kerak:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Brauzerda oching: **http://127.0.0.1:8000/docs** — bu yerda Swagger UI
orqali API'ni sinab ko'rishingiz mumkin.

### Tekshirish:
- `http://127.0.0.1:8000/` → `{"status":"ok","message":"Gaming Shop backend ishlayapti"}`
- `http://127.0.0.1:8000/api/products` → 24 ta mahsulot ro'yxati JSON
  formatida chiqishi kerak (birinchi marta ishga tushganda avtomatik
  bazaga yoziladi).

Backend birinchi marta ishga tushganda, loyihaning ROOT papkasida
`gaming_shop.db` fayli avtomatik yaratiladi va boshlang'ich mahsulotlar
(PUBG, Mobile Legends, Free Fire, Telegram Stars, Telegram Premium)
namunaviy narxlar bilan bazaga yoziladi.

> ⚠️ **Eslatma:** Bazaga yozilgan narxlar — **namunaviy (demo) narxlar**.
> Ular real ish uchun emas, tizimning to'liq ishlashini ko'rsatish uchun.
> Keyinchalik (7-bosqich, Admin panel) ularni qulay tarzda o'zgartira
> olasiz. Hozircha, agar tezroq o'zgartirmoqchi bo'lsangiz, DB Browser
> for SQLite kabi dastur bilan `gaming_shop.db` faylini ochib, `products`
> jadvalidagi `price` ustunini tahrirlashingiz mumkin.

---

## 🤖 4-QADAM: Botni ishga tushirish

**Backend ishlab turgan holda**, YANGI terminal oching:

```powershell
cd bot
venv\Scripts\activate
python bot.py
```

**Kutilgan natija:**

```
🤖 Gaming Shop boti ishga tushmoqda...
To'xtatish uchun: Ctrl + C
```

### Tekshirish:
1. Telegram'da botingizni toping (username orqali) va **/start** bosing.
2. Bot sizni salomlashishi va asosiy menyuni (ReplyKeyboard tugmalari)
   ko'rsatishi kerak.
3. **🛒 Xarid qilish** → kategoriya tanlang (masalan **🎮 PUBG Mobile**) →
   mahsulotlar ro'yxati narxlari bilan chiqishi kerak.
4. **💰 Balans** → `0 so'm` ko'rsatishi kerak (yangi foydalanuvchi uchun).
5. **👤 Profil** → Telegram ID, username, balans, buyurtmalar soni (0),
   takliflar soni (0) va ro'yxatdan o'tgan sana ko'rsatilishi kerak.
6. **🎁 Promo**, **👥 Referral**, **📦 Buyurtmalarim** — hozircha "keyingi
   bosqichda qo'shiladi" degan xabar chiqishi kerak (bu normal, chunki
   ular hali ishlab chiqilmagan).
7. Menyudan tashqari, tasodifiy matn yozib ko'ring (masalan "salom") —
   bot "Kechirasiz, tushunmadim" deb javob berishi kerak.

---

## 🛠 Xatoliklarni bartaraf etish (Troubleshooting)

| Muammo | Yechim |
|---|---|
| `BOT_TOKEN topilmadi!` xatoligi | `.env` fayli ROOT papkada borligini va `BOT_TOKEN=` to'ldirilganini tekshiring |
| `ModuleNotFoundError: No module named 'fastapi'` (yoki `telebot`) | Virtual muhitni faollashtirganingizni (`venv\Scripts\activate`) va `pip install -r requirements.txt` bajarganingizni tekshiring |
| Bot ishga tushmayapti, lekin xato ham chiqmayapti | Internetga ulanish borligini tekshiring; noto'g'ri token bo'lsa, Telegram API 401 xatosini qaytaradi |
| `/api/products` bo'sh ro'yxat qaytaryapti | `gaming_shop.db` faylini o'chirib, backend'ni qayta ishga tushiring (avtomatik qayta yaratiladi va to'ldiriladi) |
| Bot va backend turli balansni ko'rsatayotgandek tuyulsa | Ikkalasi ham loyihaning ROOT papkasidagi bitta `gaming_shop.db` faylidan foydalanadi — agar loyiha papkasini ko'chirgan bo'lsangiz, ikkalasini ham to'xtatib qayta ishga tushiring |

---

## ✅ 1-BOSQICH holati

Bajarildi:
- [x] Backend (FastAPI) + SQLAlchemy + SQLite
- [x] To'liq database sxemasi (barcha bosqichlar uchun jadvallar tayyor)
- [x] Telegram bot (ReplyKeyboard menyu)
- [x] Foydalanuvchini ro'yxatga olish (`/start`)
- [x] Mahsulotlarni ko'rish (bot orqali, kategoriya bo'yicha)
- [x] `/api/products` REST endpoint
- [x] Balansni ko'rish
- [x] Profilni ko'rish
- [x] Bot va backend bitta database va bitta sxemadan foydalanadi

Hali qo'shilmagan (keyingi bosqichlarda):
- [x] Balans to'ldirish (chek yuborish + admin tasdiqlashi) — 2-bosqich
- [ ] To'liq buyurtma berish jarayoni — 3-bosqich
- [ ] Admin buyurtmalarni boshqarishi — 4-bosqich
- [ ] React frontend — 5-bosqich
- [ ] Telegram Mini App auth — 6-bosqich
- [ ] Admin web panel — 7-bosqich
- [ ] Promo + Referral — 8-bosqich
- [ ] Statistika — 9-bosqich
- [ ] Xavfsizlik + testing + production deploy — 10-bosqich

---

Test qilib bo'lgach va hammasi ishlasa, davom etish uchun shunchaki
**"DAVOM ET"** deb yozing — men 2-BOSQICHni (Balans to'ldirish + chek +
admin Telegram kanali + tasdiqlash/rad etish) boshlayman.


---

# 💳 2-BOSQICH: Balans to'ldirish

## Oqim
1. Foydalanuvchi **💰 Balans → 💳 Balans to'ldirish** bosadi, summani kiritadi.
2. Bot karta ma'lumotlarini (`.env` dan) ko'rsatadi, foydalanuvchi **chek rasmini** yuboradi.
3. So'rov bazaga `pending` bo'lib yoziladi va admin kanaliga chek rasmi + ✅/❌ tugmalari bilan yuboriladi.
4. Admin **✅ TASDIQLASH** bosadi -> balansga summa qo'shiladi, `balance_transactions` ga yoziladi, foydalanuvchiga xabar ketadi. **❌ RAD ETISH** -> balans o'zgarmaydi, foydalanuvchiga xabar ketadi.

## Yangi fayllar
- `backend/services/balance_service.py` — balans bo'yicha YAGONA biznes-logika (bot ham, keyinroq API ham shuni ishlatadi)
- `backend/test_balance_service.py` — servisni vaqtinchalik bazada sinaydigan test
- `bot/notifications.py`, `bot/handlers/admin.py`, `bot/logger.py`

## Xavfsizlik
- Tugmalarni faqat `ADMIN_TELEGRAM_IDS` dagilar bosa oladi.
- Ikki marta tasdiqlash yo'q: `UPDATE ... WHERE status='pending'` (atomik).
- Balans `SET balance = balance + X` bilan o'zgaradi (parallel so'rovlarda xavfsiz).
- Barcha admin amallari `admin_logs` jadvaliga yoziladi.

## Admin kanali
1. Telegram'da **yopiq (private)** kanal yarating (chek rasmlari maxfiy!).
2. Botni kanalga **administrator** qilib qo'shing (xabar yuborish huquqi bilan).
3. Kanal ID'sini oling: kanaldan biror xabarni **@getidsbot** ga forward qiling. ID `-100...` bilan boshlanadi.
4. `.env` da `ADMIN_CHANNEL_ID=-100...` qiling va botni qayta ishga tushiring.
Kanal ishlamasa, bot so'rovni har bir adminga shaxsiy xabar qilib yuboradi (zaxira yo'l).

## Loglar
`logs/bot.log` (hammasi) va `logs/error.log` (faqat xatolar) — loyiha papkasida avtomatik yaratiladi.
