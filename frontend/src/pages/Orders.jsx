import { useEffect, useState } from 'react';
import { AuthGate } from '../components/AuthGate.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { api, ApiError } from '../api/client.js';
import { getCategory, formatPrice } from '../api/categories.js';
import { CategoryIcon } from '../components/CategoryIcon.jsx';

const STATUS_LABELS = {
  pending: '⏳ Kutilmoqda',
  approved: '✅ Tasdiqlangan',
  processing: '⚙️ Jarayonda',
  completed: '✅ Bajarildi',
  rejected: '❌ Rad etilgan',
  refunded: '↩️ Qaytarilgan',
};

function OrdersList() {
  const { token } = useAuth();
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let cancelled = false;
    api
      .getOrders(token)
      .then((data) => {
        if (cancelled) return;
        setOrders(Array.isArray(data) ? data : []);
        setStatus('ready');
      })
      .catch((err) => {
        if (cancelled) return;
        setErrorMessage(err instanceof ApiError ? err.message : "Noma'lum xatolik yuz berdi.");
        setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (status === 'loading') {
    return (
      <div className="state-box">
        <p>Buyurtmalar yuklanmoqda...</p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="state-box state-box--error">
        <p>⚠️ {errorMessage}</p>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="state-box">
        <p>📦 Sizda hali buyurtmalar yo'q.</p>
      </div>
    );
  }

  return (
    <div className="orders-list">
      {orders.map((order) => {
        const cat = getCategory(order.category);
        return (
          <div key={order.order_number} className="order-row" style={{ '--accent': `var(${cat?.colorVar || '--gold'})` }}>
            <div className="order-row__icon">
              <CategoryIcon slug={order.category} size={22} />
            </div>
            <div className="order-row__main">
              <span className="order-row__number">#{order.order_number}</span>
              <span className="order-row__product">{order.product_name}</span>
            </div>
            <div className="order-row__meta">
              <span className="order-row__price">{formatPrice(order.price)}</span>
              <span className="order-row__status">{STATUS_LABELS[order.status] || order.status}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function Orders({ botLink }) {
  return (
    <AuthGate
      icon="📦"
      title="Buyurtmalarim"
      guestDescription="Bu yerda buyurtmalaringiz tarixini ko'rish mumkin bo'ladi."
      botLink={botLink}
    >
      {() => (
        <section className="section">
          <div className="container">
            <h1 className="section__title">📦 Buyurtmalarim</h1>
            <OrdersList />
          </div>
        </section>
      )}
    </AuthGate>
  );
}
