/**
 * Backend (FastAPI) bilan bog'lanish uchun kichik yordamchi.
 *
 * API manzili .env (loyihaning ROOT papkasidagi) dagi VITE_API_URL dan
 * olinadi - shuning uchun backend boshqa portda yoki serverda ishlasa,
 * frontend kodini o'zgartirish shart emas.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { token, ...options } = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch (networkError) {
    throw new ApiError(
      "Backend'ga ulanib bo'lmadi. Backend ishga tushirilganini tekshiring.",
      0
    );
  }

  if (!response.ok) {
    let detail = `So'rov muvaffaqiyatsiz (${response.status})`;
    try {
      const data = await response.json();
      if (data && data.detail) detail = data.detail;
    } catch {
      /* javob JSON emas - standart xabar qoladi */
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  getProducts: (category) =>
    request(category ? `/api/products?category=${encodeURIComponent(category)}` : '/api/products'),

  authTelegram: (initData) =>
    request('/api/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ init_data: initData }),
    }),

  getMe: (token) => request('/api/me', { token }),

  getBalance: (token) => request('/api/balance', { token }),

  getOrders: (token) => request('/api/orders', { token }),
};

export { ApiError, BASE_URL };
