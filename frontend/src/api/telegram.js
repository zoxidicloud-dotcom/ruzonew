/**
 * Telegram WebApp SDK (https://telegram.org/js/telegram-web-app.js) bilan
 * ishlash uchun kichik yordamchi. Sayt Telegramdan tashqarida (oddiy
 * brauzerda) ochilganda window.Telegram mavjud bo'lmaydi yoki initData
 * bo'sh bo'ladi - bu funksiyalar shu holatni xavfsiz boshqaradi.
 */

export function getTelegramWebApp() {
  return typeof window !== 'undefined' ? window.Telegram?.WebApp : undefined;
}

export function getInitData() {
  return getTelegramWebApp()?.initData || '';
}

export function isInsideTelegram() {
  return Boolean(getInitData());
}

export function markReady() {
  const webApp = getTelegramWebApp();
  if (!webApp) return;
  try {
    webApp.ready();
    webApp.expand();
  } catch {
    /* eski Telegram versiyasida bu metodlar bo'lmasligi mumkin - jim o'tamiz */
  }
}
