/**
 * Kategoriyalar haqidagi ko'rinish ma'lumotlari (nom, rang).
 *
 * Bu backend/services/order_service.py dagi CATEGORIES bilan MOS bo'lishi
 * kerak (category "slug" qiymatlari bir xil bo'lishi shart, chunki ular
 * API'dan keladigan mahsulotlarning "category" maydoni bilan solishtiriladi).
 * Frontend Python kodini import qila olmagani uchun bu kichik jadval shu
 * yerda alohida saqlanadi - u shunchaki ism/rang, biznes-logika emas.
 */

export const CATEGORIES = [
  { slug: 'pubg', title: 'PUBG Mobile', short: 'PUBG', colorVar: '--c-pubg' },
  { slug: 'mobile_legends', title: 'Mobile Legends', short: 'ML', colorVar: '--c-ml' },
  { slug: 'free_fire', title: 'Free Fire', short: 'Free Fire', colorVar: '--c-freefire' },
  { slug: 'telegram_stars', title: 'Telegram Stars', short: 'Stars', colorVar: '--c-stars' },
  { slug: 'telegram_premium', title: 'Telegram Premium', short: 'Premium', colorVar: '--c-premium' },
];

export function getCategory(slug) {
  return CATEGORIES.find((c) => c.slug === slug) || null;
}

export function formatPrice(amount) {
  const rounded = Math.round(Number(amount) || 0);
  // toLocaleString('ru-RU') minglik ajratgichi sifatida "uzilmaydigan bo'sh
  // joy" (U+00A0) ishlatadi, ko'zga oddiy bo'sh joydek ko'rinsa ham. Buni
  // botdagi format_price() bilan bir xil ko'rinishda bo'lishi uchun oddiy
  // bo'sh joyga (U+0020) almashtiramiz.
  const withNbsp = rounded.toLocaleString('ru-RU');
  const normalized = withNbsp.replace(/\u00A0/g, ' ');
  return `${normalized} so'm`;
}
