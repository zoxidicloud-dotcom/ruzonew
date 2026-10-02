import { useAuth } from '../context/AuthContext.jsx';
import { ComingSoon } from './ComingSoon.jsx';

/**
 * Autentifikatsiya talab qiladigan sahifalar (Balans, Buyurtmalar, Profil)
 * uchun umumiy "himoyachi". To'rtta holatni birday boshqaradi, shuning
 * uchun har bir sahifa bu mantiqni o'zida takrorlamaydi.
 */
export function AuthGate({ icon, title, guestDescription, botLink, children }) {
  const { status, me, errorMessage } = useAuth();

  if (status === 'checking') {
    return (
      <section className="section">
        <div className="container state-box">
          <p>Yuklanmoqda...</p>
        </div>
      </section>
    );
  }

  if (status === 'guest') {
    return (
      <ComingSoon
        icon={icon}
        title={title}
        description={guestDescription}
        note="Bu bo'lim faqat Telegram Mini App orqali ochilganda ishlaydi (saytni to'g'ridan-to'g'ri brauzerda ochganda emas)."
        botLink={botLink}
      />
    );
  }

  if (status === 'error') {
    return (
      <section className="section">
        <div className="container state-box state-box--error">
          <p>⚠️ {errorMessage}</p>
        </div>
      </section>
    );
  }

  return children(me);
}
