import { AuthGate } from '../components/AuthGate.jsx';
import { formatPrice } from '../api/categories.js';

export function Balance({ botLink }) {
  return (
    <AuthGate
      icon="💰"
      title="Balans"
      guestDescription="Bu yerda balansingizni ko'rish mumkin bo'ladi."
      botLink={botLink}
    >
      {(me) => (
        <section className="section">
          <div className="container">
            <h1 className="section__title">💰 Balans</h1>
            <div className="balance-card">
              <span className="balance-card__label">Joriy balansingiz</span>
              <span className="balance-card__amount">{formatPrice(me.balance)}</span>
              <p className="balance-card__hint">
                Balansni to'ldirish uchun hozircha Telegram botimizdan foydalaning
                (💰 Balans → 💳 Balans to'ldirish).
              </p>
              {botLink && (
                <a className="coming-soon__cta" href={botLink} target="_blank" rel="noreferrer">
                  Telegram botni ochish
                </a>
              )}
            </div>
          </div>
        </section>
      )}
    </AuthGate>
  );
}
