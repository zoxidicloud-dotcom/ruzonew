import { useState } from 'react';

const LINKS = [
  { id: 'home', label: 'Bosh sahifa' },
  { id: 'products', label: 'Mahsulotlar' },
  { id: 'orders', label: 'Buyurtmalar' },
  { id: 'balance', label: 'Balans' },
  { id: 'profile', label: 'Profil' },
];

export function Navbar({ shopName, activeView, onNavigate }) {
  const [open, setOpen] = useState(false);

  function go(id) {
    onNavigate(id);
    setOpen(false);
  }

  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <button className="navbar__brand" onClick={() => go('home')} aria-label="Bosh sahifa">
          <span className="navbar__brand-mark">{shopName.slice(0, 1).toUpperCase()}</span>
          <span className="navbar__brand-name">{shopName}</span>
        </button>

        <nav className="navbar__links navbar__links--desktop" aria-label="Asosiy navigatsiya">
          {LINKS.map((link) => (
            <button
              key={link.id}
              className={`navbar__link ${activeView === link.id ? 'is-active' : ''}`}
              onClick={() => go(link.id)}
            >
              {link.label}
            </button>
          ))}
        </nav>

        <button
          className="navbar__burger"
          aria-label="Menyuni ochish"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      {open && (
        <nav className="navbar__links navbar__links--mobile" aria-label="Mobil navigatsiya">
          {LINKS.map((link) => (
            <button
              key={link.id}
              className={`navbar__link ${activeView === link.id ? 'is-active' : ''}`}
              onClick={() => go(link.id)}
            >
              {link.label}
            </button>
          ))}
        </nav>
      )}
    </header>
  );
}
