import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api, ApiError } from '../api/client.js';
import { getInitData, markReady } from '../api/telegram.js';

const AuthContext = createContext(null);
const TOKEN_STORAGE_KEY = 'gaming_shop_session_token';

/**
 * Autentifikatsiya holatlari:
 *   checking      - hali tekshirilmoqda (sahifa ochilgan zahoti)
 *   authenticated - Telegram orqali muvaffaqiyatli kirildi, `me` to'ldirilgan
 *   guest         - sayt Telegram'dan TASHQARIDA (oddiy brauzerda) ochilgan -
 *                   bu xato emas, shunchaki login yo'q
 *   error         - Telegram ichida ochilgan, lekin initData yaroqsiz yoki
 *                   backend bilan bog'lanishda muammo chiqdi
 */
export function AuthProvider({ children }) {
  const [status, setStatus] = useState('checking');
  const [token, setToken] = useState('');
  const [me, setMe] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    markReady();
    let cancelled = false;

    async function authenticateViaTelegram(initData) {
      const { token: newToken } = await api.authTelegram(initData);
      const profile = await api.getMe(newToken);
      if (cancelled) return;
      sessionStorage.setItem(TOKEN_STORAGE_KEY, newToken);
      setToken(newToken);
      setMe(profile);
      setStatus('authenticated');
    }

    async function init() {
      const initData = getInitData();
      const existingToken = sessionStorage.getItem(TOKEN_STORAGE_KEY);

      // 1) Avval saqlangan sessiyani sinab ko'ramiz (sahifa qayta
      //    yuklanganda Telegram bilan qayta so'zlashmaslik uchun).
      if (existingToken) {
        try {
          const profile = await api.getMe(existingToken);
          if (cancelled) return;
          setToken(existingToken);
          setMe(profile);
          setStatus('authenticated');
          return;
        } catch {
          sessionStorage.removeItem(TOKEN_STORAGE_KEY);
          // Davom etamiz - agar Telegram ichida bo'lsak, pastda qaytadan
          // (jimgina) login qilib ko'ramiz.
        }
      }

      // 2) Telegram'dan tashqarida ochilgan - bu xato emas, "mehmon" rejimi.
      if (!initData) {
        if (!cancelled) setStatus('guest');
        return;
      }

      // 3) Telegram ichidamiz - initData orqali kirishga harakat qilamiz.
      try {
        await authenticateViaTelegram(initData);
      } catch (err) {
        if (cancelled) return;
        setStatus('error');
        setErrorMessage(err instanceof ApiError ? err.message : 'Kirishda xatolik yuz berdi.');
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const profile = await api.getMe(token);
      setMe(profile);
    } catch {
      /* fon jarayonida yangilashda xato bo'lsa, joriy ma'lumotni saqlab qolamiz */
    }
  }, [token]);

  const value = { status, token, me, errorMessage, refresh };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth() faqat <AuthProvider> ichida ishlatilishi mumkin');
  }
  return ctx;
}
