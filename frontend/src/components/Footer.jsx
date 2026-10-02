export function Footer({ shopName, botUsername }) {
  const year = new Date().getFullYear();
  const botLink = botUsername ? `https://t.me/${botUsername}` : null;

  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div>
          <p className="footer__brand">{shopName}</p>
          <p className="footer__tagline">Gaming uchun kerakli mahsulotlar bir joyda.</p>
        </div>

        <div className="footer__links">
          {botLink ? (
            <a href={botLink} target="_blank" rel="noreferrer" className="footer__bot-link">
              💬 Telegram botimiz
            </a>
          ) : (
            <span className="footer__bot-link footer__bot-link--muted">
              Telegram bot (.env da VITE_BOT_USERNAME sozlansin)
            </span>
          )}
        </div>

        <p className="footer__copy">© {year} {shopName}. Barcha huquqlar himoyalangan.</p>
      </div>
    </footer>
  );
}
