import { AuthGate } from '../components/AuthGate.jsx';
import { formatPrice } from '../api/categories.js';

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}.${month}.${year}`;
}

export function Profile({ botLink }) {
  return (
    <AuthGate
      icon="👤"
      title="Profil"
      guestDescription="Bu yerda hisobingiz ma'lumotlarini ko'rish mumkin bo'ladi."
      botLink={botLink}
    >
      {(me) => (
        <section className="section">
          <div className="container">
            <h1 className="section__title">👤 Profil</h1>
            <div className="profile-card">
              <div className="profile-row">
                <span className="profile-row__label">🆔 Telegram ID</span>
                <span className="profile-row__value">{me.telegram_id}</span>
              </div>
              <div className="profile-row">
                <span className="profile-row__label">👤 Username</span>
                <span className="profile-row__value">
                  {me.username ? `@${me.username}` : '— (username yo\u2018q)'}
                </span>
              </div>
              <div className="profile-row">
                <span className="profile-row__label">💰 Balans</span>
                <span className="profile-row__value">{formatPrice(me.balance)}</span>
              </div>
              <div className="profile-row">
                <span className="profile-row__label">📦 Buyurtmalar soni</span>
                <span className="profile-row__value">{me.orders_count}</span>
              </div>
              <div className="profile-row">
                <span className="profile-row__label">👥 Taklif qilganlar soni</span>
                <span className="profile-row__value">{me.referrals_count}</span>
              </div>
              <div className="profile-row">
                <span className="profile-row__label">🎁 Referral kodingiz</span>
                <span className="profile-row__value">
                  <code>{me.referral_code}</code>
                </span>
              </div>
              <div className="profile-row">
                <span className="profile-row__label">📅 Ro'yxatdan o'tgan sana</span>
                <span className="profile-row__value">{formatDate(me.created_at)}</span>
              </div>
            </div>
          </div>
        </section>
      )}
    </AuthGate>
  );
}
