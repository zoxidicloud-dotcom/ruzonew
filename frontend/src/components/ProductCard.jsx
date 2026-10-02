import { formatPrice } from '../api/categories.js';

export function ProductCard({ product, colorVar, botLink }) {
  return (
    <div className="product-card" style={{ '--accent': `var(${colorVar})` }}>
      <div className="product-card__top">
        <span className="product-card__name">{product.name}</span>
        {product.description && (
          <span className="product-card__desc">{product.description}</span>
        )}
      </div>
      <div className="product-card__bottom">
        <span className="product-card__price">{formatPrice(product.price)}</span>
        {botLink ? (
          <a className="product-card__buy" href={botLink} target="_blank" rel="noreferrer">
            Botda xarid qilish
          </a>
        ) : (
          <span className="product-card__buy product-card__buy--muted">Telegram botda xarid qiling</span>
        )}
      </div>
    </div>
  );
}
