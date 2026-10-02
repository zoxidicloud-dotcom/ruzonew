# 🎮 Gaming Shop — 6-BOSQICH (1-5-bosqichlar ustiga qurilgan)

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
- [x] To'liq buyurtma berish jarayoni — 3-bosqich
- [x] Admin buyurtmalarni boshqarishi — 4-bosqich
- [x] React frontend — 5-bosqich
- [x] Telegram Mini App auth — 6-bosqich
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


---

# 🛒 3-BOSQICH: To'liq buyurtma berish jarayoni

## Oqim
1. **🛒 Xarid qilish** → kategoriya (PUBG, Mobile Legends, Free Fire, Stars, Premium) → mahsulotlar **inline tugmalar** bilan chiqadi.
2. Mahsulot tanlanadi → bot kerakli ma'lumotlarni ketma-ket so'raydi:
   - PUBG: Nickname, PUBG ID
   - Mobile Legends: Nickname, User ID, Zone ID
   - Free Fire: Nickname, Player ID
   - Telegram Stars / Premium: Telegram username
3. Har bir maydon **darhol tekshiriladi** (masalan, ID faqat raqamlardan iborat bo'lishi kerak) — xato bo'lsa, o'sha maydon qaytadan so'raladi.
4. **Tasdiqlash ekrani**: barcha ma'lumot + narx + joriy balans, ✅/❌ tugmalar bilan.
5. ✅ bosilsa: `order_service.create_order()` orqali **balansdan pul yechilmasdan** `pending` buyurtma yaratiladi, admin kanaliga yuboriladi.

**Muhim biznes qoida (loyiha talabi, 11-band):** buyurtma yaratilganda balans yechilmaydi. Balans faqat admin buyurtmani tasdiqlaganda yechiladi — bu **4-bosqichda** qo'shiladi.

## Yangi fayllar
- `backend/services/order_service.py` — buyurtma bo'yicha YAGONA biznes-logika: mahsulot turlari, maydon validatorlari, dublikat/limit tekshiruvi, buyurtma yaratish
- `backend/test_order_service.py` — servisni sinaydigan test (validatsiya, dublikat, limit, narx o'zgarishi, parallel so'rovlar)
- `bot/state.py` — buyurtma jarayonining vaqtinchalik holati (xotirada)
- `bot/handlers/orders.py` — "📦 Buyurtmalarim" haqiqiy implementatsiyasi

## Himoya choralari
- **Narx o'zgarishi:** foydalanuvchi ko'rgan narx bilan tasdiqlash paytidagi narx solishtiriladi (`PriceChanged`).
- **Dublikat:** 60 soniya ichida bir xil mahsulot + bir xil ma'lumotlar bilan qayta yuborilgan buyurtma rad etiladi.
- **Limit:** bir foydalanuvchida bir vaqtda 5 tadan ortiq "pending" buyurtma bo'la olmaydi.
- **Balans:** buyurtma yaratishda faqat YETARLIMI tekshiriladi, pul yechilmaydi.

## Admin kanaliga xabar
Yangi buyurtma haqida xabar boradi (mahsulot, narx, o'yinchi ma'lumotlari). **Boshqarish tugmalari (✅ TASDIQLASH / ⚙️ BAJARILDI / ❌ RAD ETISH) 4-bosqichda qo'shiladi** — hozircha xabar faqat ma'lumot uchun.

## Test qilish
```
cd backend
python test_order_service.py
```
Oxirida `HAMMA TESTLAR O'TDI` chiqishi kerak.


---

# ⚙️ 4-BOSQICH: Admin buyurtmalarni boshqarishi

## Buyurtma holatlari va o'tishlar
```
pending --[✅ TASDIQLASH]--> approved --[⚙️ BAJARILDI]--> completed
   |                            |
   [❌ RAD ETISH]               [↩️ QAYTARISH]
   v                            v
rejected                    refunded
```
- **TASDIQLASH**: balansdan narx **yechiladi** (`balance_transactions` ga `purchase` sifatida yoziladi), admin xabaridagi tugmalar ⚙️ BAJARILDI / ↩️ QAYTARISH ga almashadi.
- **BAJARILDI**: faqat admin mahsulotni qo'lda yuborgandan keyin bosiladi. Balansga tegmaydi.
- **RAD ETISH**: faqat `pending` holatidagi buyurtmaga. Balansga tegmaydi (u hali yechilmagan).
- **QAYTARISH (refund)**: faqat `approved` holatidagi (hali bajarilmagan) buyurtmaga. Balansga pul **to'liq qaytariladi** (`refund` sifatida yoziladi).

Har bir tugma bosilganda foydalanuvchiga mos xabar boradi va admin kanalidagi xabar yangi holatga mos tugmalar bilan yangilanadi.

## Muhim: balans va buyurtma holati BIR XIL tranzaksiyada
`order_service.py` buyurtma holatini o'zgartiradi, `balance_service.py` (2-bosqichdan, o'zgarishsiz) balansni o'zgartiradi — ikkalasi **bitta `db.commit()` bilan** birga bajariladi (`bot/handlers/admin.py` da). Shu tufayli "buyurtma tasdiqlandi, lekin pul yechilmadi" (yoki aksincha) degan holat FIZIK JIHATDAN yuzaga kela olmaydi.

## Ikki marta bosishdan himoya
Balans to'ldirishdagi kabi, bu yerda ham atomik `UPDATE ... WHERE status='X'` ishlatiladi. Ikki admin bir vaqtda bitta buyurtmani tasdiqlasa, faqat bittasi o'tadi, ikkinchisi "allaqachon ko'rib chiqilgan" xabarini oladi va balans FAQAT BIR MARTA yechiladi.

## Yangi/o'zgargan fayllar
- `backend/services/order_service.py` — `claim_order_approval/rejection/completion/refund()` funksiyalari qo'shildi
- `backend/test_order_service.py` — admin amallari va parallel tasdiqlash testlari qo'shildi
- `bot/notifications.py` — `order_caption` endi joriy holatga mos tugma va admin ismini ko'rsatadi
- `bot/handlers/admin.py` — `oadmin:approve/reject/complete/refund:<id>` callbacklarini qayta ishlaydi

## Test qilish
```
cd backend
python test_order_service.py
```
Oxirida `HAMMA TESTLAR O'TDI` chiqishi kerak (jami testlar soni ko'paydi).

## Botda qo'lda sinash
1. Buyurtma bering (3-bosqichdagidek) → admin kanalida ✅/❌ tugmalari bilan xabar keladi.
2. **✅ TASDIQLASH** bosing → foydalanuvchiga "tasdiqlandi" xabari, balansdan narx yechiladi, admin xabari ⚙️/↩️ tugmalariga almashadi.
3. **⚙️ BAJARILDI** bosing → foydalanuvchiga "BAJARILDI" xabari, buyurtma holati "✅ Bajarildi" ga o'zgaradi (📦 Buyurtmalarim'da tekshiring).
4. Yangi buyurtma bering, ✅ TASDIQLASH bosing, so'ng **↩️ QAYTARISH** bosing → balans to'liq qaytishi kerak (💰 Balans'da tekshiring).
5. Yangi buyurtma bering, **❌ RAD ETISH** bosing → balans o'zgarmasligi kerak.
6. Tasdiqlangan/bajarilgan buyurtma tugmasini yana bosishga urinib ko'ring → "allaqachon ko'rib chiqilgan" chiqishi kerak.


---

# 🖥️ 5-BOSQICH: React frontend (sayt)

## Nima qo'shildi
`frontend/` papkasida to'liq React + Vite sayti:
- **Bosh sahifa**: hero (sarlavha, tavsif, "🛒 Xarid qilish" tugmasi), 5 ta kategoriya kartasi, "Nega aynan biz?" afzalliklar bo'limi.
- **Mahsulotlar sahifasi**: backend'dan (`GET /api/products`) **jonli** narxlarni oladi, kategoriya bo'yicha filtrlaydi, har bir mahsulot uchun "Botda xarid qilish" tugmasi (Telegram botga olib boradi).
- **Balans / Buyurtmalarim / Profil**: hozircha "keyingi bosqichda faollashadi" degan halol xabar bilan (chunki bularga Telegram orqali login kerak - bu 6-bosqich).

## Dizayn g'oyasi
Sotilayotgan narsa aslida **raqamli valyuta** (UC, Diamonds, Stars) - shuning uchun rang palitrasi odatiy "gaming neon" emas, balki **"valyuta/tanga"** tuyg'usiga asoslangan (issiq oltin asosiy rang). Har bir kategoriya esa o'zining haqiqiy o'yin brendiga yaqin rangdan foydalanadi (PUBG - amber, Mobile Legends - binafsha, Free Fire - olov-qizil, Telegram Premium - Telegram ko'k rangi).

## .env ga qo'shimcha (MUHIM)
Vite xavfsizlik sababli faqat `VITE_` bilan boshlangan o'zgaruvchilarni frontendga ochadi, shuning uchun `.env` faylingizga **qo'lda** quyidagi 3 qatorni qo'shing (`.env.example`da ham bor):
```
VITE_API_URL=http://127.0.0.1:8000
VITE_SHOP_NAME=Gaming Shop
VITE_BOT_USERNAME=your_bot_username
```
`VITE_BOT_USERNAME` - botingiz username'i (@ belgisisiz) - bu bo'lmasa, "Telegram botni ochish" tugmalari ko'rinmaydi.

## Ishga tushirish (Windows + VS Code)
Backend ishlab turishi kerak (mahsulotlar shundan olinadi). Yangi Command Prompt:
```
cd frontend
npm install
npm run dev
```
Terminalda ko'rsatilgan manzilni (odatda `http://localhost:5173`) brauzerda oching.

## Texnik qaror: React Router ishlatilmadi
Sahifalar orasida oddiy **holatga asoslangan** navigatsiya ishlatildi (`App.jsx` dagi `useState`), alohida `react-router-dom` kutubxonasisiz - bu bosqichdagi 5 ta sahifa uchun bu yetarli va sodda. Agar keyinchalik har bir sahifa uchun alohida URL (masalan `/mahsulotlar`) kerak bo'lsa, buni keyinroq qo'shish oson.

## Qanday tekshirilgan
Bu muhitda `npm install` uchun internet yo'q edi, shuning uchun kod boshqacha yo'l bilan tekshirildi: barcha `.jsx` fayllar `esbuild` orqali haqiqiy bundle qilindi (0 xato), so'ng **Playwright** orqali haqiqiy brauzerda (Chromium) ochilib, matn/rasm darajasida tekshirildi - jumladan soxta API bilan mahsulotlar to'g'ri chizilishi, backend o'chiq bo'lganda tushunarli xato ko'rsatilishi, mobil ko'rinishda burger-menyu ishlashi. Shu tekshiruv davomida narx formatlashdagi kichik xato (oddiy bo'sh joy o'rniga "uzilmaydigan bo'sh joy" belgisi) topilib, tuzatildi.


---

# 🔐 6-BOSQICH: Telegram Mini App autentifikatsiyasi

## Nima qo'shildi
- **Backend**: `auth.py` (Telegram `initData`ni tekshirish + sessiya tokeni), `deps.py` (FastAPI uchun "joriy foydalanuvchi" dependency), yangi endpointlar: `POST /api/auth/telegram`, `GET /api/me`, `GET /api/balance`, `GET /api/orders`.
- **Bot**: asosiy menyuga **"🌐 Saytni ochish"** tugmasi qo'shildi (agar `.env`da `WEBSITE_URL` sozlangan bo'lsa) - bosilganda sayt Telegram ICHIDA (Mini App sifatida) ochiladi.
- **Frontend**: Telegram WebApp SDK ulandi, `AuthContext` (avtomatik login), **Balans/Buyurtmalar/Profil** sahifalari endi haqiqiy ma'lumot ko'rsatadi (Telegram orqali ochilganda).
- **Umumiy foydalanuvchi servisi**: `backend/services/user_service.py` - foydalanuvchini ro'yxatdan o'tkazish logikasi endi FAQAT bitta joyda (ilgari bot buni o'zida alohida yozgan edi - bu kamchilik shu bosqichda tuzatildi).

## Qanday ishlaydi (xavfsizlik)
Telegram har bir Mini App ochilishida `initData` deb nomlangan, **botning tokeni bilan raqamli imzolangan** ma'lumot beradi. Backend shu imzoni o'zi hisoblab, Telegramnikiga solishtiradi (`HMAC-SHA256`, Telegramning rasmiy algoritmi). Agar mos kelmasa - so'rov rad etiladi. Shu tufayli hech kim o'zini boshqa foydalanuvchi qilib ko'rsata olmaydi (buyruqdagi 31-band: "Fake user ID bilan kirishga yo'l qo'yilmasin" - aynan shu bajarildi).

Tasdiqlangan foydalanuvchi uchun backend o'zi imzolagan, 7 kunlik muddatli **sessiya tokeni** beradi (JWT emas - qo'shimcha kutubxona shart bo'lmasligi uchun ataylab oddiy, lekin bir xil xavfsizlik prinsipida: `HMAC` bilan imzolangan). Frontend bu tokenni brauzer xotirasida (`sessionStorage`) saqlaydi va har bir so'rovda `Authorization: Bearer <token>` sifatida yuboradi.

## .env ga qo'shimcha (MUHIM - ikkalasi ham SHART)
```
SESSION_SECRET=uzun-tasodifiy-maxfiy-qator
WEBSITE_URL=
```
`SESSION_SECRET` uchun tasodifiy qator yarating:
```
python -c "import secrets; print(secrets.token_hex(32))"
```
Natijani `.env` dagi `SESSION_SECRET=` ga joylashtiring. **Bu bo'lmasa backend ishga tushmaydi** (atayin shunday - xavfsizlik uchun zaif standart qiymat berilmagan).

`WEBSITE_URL` - buni hozircha bo'sh qoldirsangiz ham bo'ladi (pastga qarang).

## Mini App'ni HAQIQIY Telegram'da sinash uchun: ngrok kerak
Telegram Mini App tugmalari **faqat HTTPS** manzillarni qabul qiladi - `http://localhost:5173` ishlamaydi. Serverga joylashtirmasdan turib (10-bosqich) sinash uchun eng oson yo'l - **ngrok** (vaqtinchalik ochiq HTTPS havola beradi):

1. https://ngrok.com dan ro'yxatdan o'ting (bepul) va ngrok'ni yuklab oling.
2. Frontend (`npm run dev`) ishlab turgan holda, yangi terminalda:
   ```
   ngrok http 5173
   ```
3. Ngrok sizga `https://xxxx-xx-xx.ngrok-free.app` kabi vaqtinchalik manzil beradi - shuni nusxalang.
4. `.env` da: `WEBSITE_URL=https://xxxx-xx-xx.ngrok-free.app` qiling.
5. Botni qayta ishga tushiring (`Ctrl+C`, `python bot.py`).
6. Telegram'da botga qaytib, **"🌐 Saytni ochish"** tugmasini bosing - sayt Telegram ICHIDA ochiladi va avtomatik login bo'ladi (hech qanday parol so'ramaydi!).

> ⚠️ Ngrok'ning bepul havolasi har safar qayta ishga tushirganda O'ZGARADI - shuning uchun har safar `.env`dagi `WEBSITE_URL`ni yangilab, botni qayta ishga tushirishingiz kerak bo'ladi. Bu vaqtinchalik - 10-bosqichda (VPS'ga joylashtirish) doimiy manzil bo'ladi.

## Oddiy brauzerda sinash (ngrok'siz ham mumkin)
Saytni oddiy `http://localhost:5173` orqali ochsangiz, u Telegram'ni "ko'rmaydi" - Balans/Buyurtmalar/Profil sahifalari "Bu bo'lim faqat Telegram Mini App orqali ochilganda ishlaydi" deydi. Bu **xato emas** - bu kutilgan, to'g'ri xatti-harakat ("mehmon rejimi").

## Test qilish
```
cd backend
python test_auth.py
```
Bu `initData` tekshiruvi va sessiya tokenini **14 xil holatda** (to'g'ri, soxta, eskirgan, buzilgan va h.k.) sinaydi. Oxirida `HAMMA TESTLAR O'TDI` chiqishi kerak. Bu test uchun internet yoki boshqa hech narsa kerak emas - sof Python.

## Qanday tekshirilgan
`auth.py`dagi kriptografik tekshiruv (eng xavfsizlik-muhim qism) 14 ta haqiqiy test bilan sinovdan o'tkazildi (soxta `hash`, boshqa bot tokeni, o'zgartirilgan ma'lumot, eskirgan `initData` va h.k. - barchasi to'g'ri rad etiladi). Frontend tomoni esa Playwright orqali haqiqiy Chromium brauzerida uchta holatda tekshirildi: Telegram ichida (to'g'ri `initData` bilan - profil/balans/buyurtmalar to'g'ri ko'rsatildi), Telegram ichida soxta `initData` bilan (xato xabari to'g'ri chiqdi), va oddiy brauzerda (mehmon rejimi xabari to'g'ri chiqdi).
