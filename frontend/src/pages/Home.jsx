import { CategoryIcon } from '../components/CategoryIcon.jsx';
import { CATEGORIES } from '../api/categories.js';

const ADVANTAGES = [
  { emoji: '⚡', title: 'Tez xizmat', text: "Buyurtmalar odatda bir necha daqiqada bajariladi." },
  { emoji: '🔒', title: 'Xavfsiz to\u2018lov', text: 'Har bir to\u2018lov admin tomonidan qo\u2018lda tekshiriladi.' },
  { emoji: '💬', title: '24/7 yordam', text: 'Savollaringiz bo\u2018lsa, Telegram bot orqali doim javob olasiz.' },
  { emoji: '💳', title: 'Qulay balans tizimi', text: 'Bir marta to\u2018ldiring, istalgancha xarid qiling.' },
];

export function Home({ shopName, onNavigate }) {
  return (
    <>
      <section className="hero">
        <div className="container hero__inner">
          <div className="hero__text">
            <h1 className="hero__headline">
              Gaming uchun kerakli mahsulotlar bir joyda
            </h1>
            <p className="hero__subtitle">
              PUBG UC, Mobile Legends Diamonds, Free Fire Diamonds, Telegram Stars
              va Premium — {shopName} orqali, ishonchli va tez.
            </p>
            <div className="hero__actions">
              <button className="btn btn--primary" onClick={() => onNavigate('products')}>
                🛒 Xarid qilish
              </button>
            </div>
          </div>

          <div className="hero__vault" aria-hidden="true">
            {CATEGORIES.map((cat, i) => (
              <div
                key={cat.slug}
                className={`hero__coin hero__coin--${i}`}
                style={{ '--accent': `var(${cat.colorVar})` }}
              >
                <CategoryIcon slug={cat.slug} size={26} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section__title">Mahsulot turlari</h2>
          <div className="category-grid">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.slug}
                className="category-card"
                style={{ '--accent': `var(${cat.colorVar})` }}
                onClick={() => onNavigate('products', cat.slug)}
              >
                <span className="category-card__icon">
                  <CategoryIcon slug={cat.slug} size={30} />
                </span>
                <span className="category-card__title">{cat.title}</span>
                <span className="category-card__arrow">→</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="section section--advantages">
        <div className="container">
          <h2 className="section__title">Nega aynan biz?</h2>
          <div className="advantages-grid">
            {ADVANTAGES.map((item) => (
              <div key={item.title} className="advantage-card">
                <span className="advantage-card__emoji">{item.emoji}</span>
                <h3 className="advantage-card__title">{item.title}</h3>
                <p className="advantage-card__text">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
