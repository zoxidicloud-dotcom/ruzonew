/**
 * Har bir mahsulot kategoriyasi uchun qo'lda chizilgan SVG ikonka.
 * Tashqi rasm fayllariga bog'liq emas - internet bo'lmasa ham ishlaydi.
 */

export function CategoryIcon({ slug, size = 28 }) {
  const common = { width: size, height: size, viewBox: '0 0 32 32', fill: 'none' };

  switch (slug) {
    case 'pubg':
      // Olti burchakli nishon - UC tangasi
      return (
        <svg {...common} aria-hidden="true">
          <path
            d="M16 2 28 9v14L16 30 4 23V9z"
            fill="currentColor"
            fillOpacity="0.14"
            stroke="currentColor"
            strokeWidth="1.6"
          />
          <circle cx="16" cy="16" r="6.5" stroke="currentColor" strokeWidth="1.6" />
          <path d="M16 12v8M12.2 16h7.6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      );
    case 'mobile_legends':
      // Olmos
      return (
        <svg {...common} aria-hidden="true">
          <path
            d="M9 5h14l5 7-12 15L4 12z"
            fill="currentColor"
            fillOpacity="0.14"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path d="M4 12h24M12 5l4 7-4 15M20 5l-4 7 4 15" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
        </svg>
      );
    case 'free_fire':
      // Olov tomchisi
      return (
        <svg {...common} aria-hidden="true">
          <path
            d="M16 3c1 4-3 5.5-3 9 0 1.9 1.3 3 2.6 3 1.6 0 2.4-1.3 2.1-3 2.6 1.6 4.3 4.4 4.3 7.4 0 5-4 8.6-9 8.6s-9-3.6-9-8.6c0-6 4.3-9 6-11 .4 1.6 1.3 2.4 2 2 .8-.5.7-2.2-.2-4.2C13.6 4.4 14.9 3.4 16 3z"
            fill="currentColor"
            fillOpacity="0.16"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      );
    case 'telegram_stars':
      // Yulduz
      return (
        <svg {...common} aria-hidden="true">
          <path
            d="M16 3l3.5 8.2L28 12l-6.6 6 1.9 9.8L16 23.3 8.7 27.8l1.9-9.8L4 12l8.5-.8z"
            fill="currentColor"
            fillOpacity="0.16"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinejoin="round"
          />
        </svg>
      );
    case 'telegram_premium':
      // Telegram qog'oz samolyot + toj
      return (
        <svg {...common} aria-hidden="true">
          <path
            d="M4 15 27 5l-4 22-8-6-4 4-1-7z"
            fill="currentColor"
            fillOpacity="0.16"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <path d="M12 18l11-10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      );
    default:
      return (
        <svg {...common} aria-hidden="true">
          <circle cx="16" cy="16" r="12" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      );
  }
}
