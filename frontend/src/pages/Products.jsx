import { useEffect, useMemo, useState } from 'react';
import { api, ApiError } from '../api/client.js';
import { CATEGORIES, getCategory } from '../api/categories.js';
import { CategoryIcon } from '../components/CategoryIcon.jsx';
import { ProductCard } from '../components/ProductCard.jsx';

export function Products({ initialCategory, botLink }) {
  const [activeCategory, setActiveCategory] = useState(initialCategory || 'all');
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | ready | error
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    setActiveCategory(initialCategory || 'all');
  }, [initialCategory]);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');

    api
      .getProducts()
      .then((data) => {
        if (cancelled) return;
        setProducts(Array.isArray(data) ? data : []);
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
  }, []);

  const visibleProducts = useMemo(() => {
    if (activeCategory === 'all') return products;
    return products.filter((p) => p.category === activeCategory);
  }, [products, activeCategory]);

  const grouped = useMemo(() => {
    const map = new Map();
    for (const product of visibleProducts) {
      if (!map.has(product.category)) map.set(product.category, []);
      map.get(product.category).push(product);
    }
    return map;
  }, [visibleProducts]);

  return (
    <section className="section products-page">
      <div className="container">
        <h1 className="section__title">Mahsulotlar</h1>
        <p className="products-page__intro">
          Narxlar so'mda ko'rsatilgan. Xarid qilish uchun Telegram botimizdan foydalaning.
        </p>

        <div className="category-tabs" role="tablist" aria-label="Kategoriya filtri">
          <button
            className={`category-tab ${activeCategory === 'all' ? 'is-active' : ''}`}
            onClick={() => setActiveCategory('all')}
          >
            Barchasi
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.slug}
              className={`category-tab ${activeCategory === cat.slug ? 'is-active' : ''}`}
              style={{ '--accent': `var(${cat.colorVar})` }}
              onClick={() => setActiveCategory(cat.slug)}
            >
              <CategoryIcon slug={cat.slug} size={16} />
              {cat.short}
            </button>
          ))}
        </div>

        {status === 'loading' && (
          <div className="state-box">
            <p>Mahsulotlar yuklanmoqda...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="state-box state-box--error">
            <p>⚠️ {errorMessage}</p>
          </div>
        )}

        {status === 'ready' && visibleProducts.length === 0 && (
          <div className="state-box">
            <p>Bu bo'limda hozircha faol mahsulot yo'q.</p>
          </div>
        )}

        {status === 'ready' &&
          [...grouped.entries()].map(([categorySlug, items]) => {
            const cat = getCategory(categorySlug);
            return (
              <div key={categorySlug} className="product-group">
                {activeCategory === 'all' && (
                  <h2 className="product-group__title" style={{ '--accent': `var(${cat?.colorVar || '--gold'})` }}>
                    <CategoryIcon slug={categorySlug} size={20} />
                    {cat?.title || categorySlug}
                  </h2>
                )}
                <div className="product-grid">
                  {items.map((product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      colorVar={cat?.colorVar || '--gold'}
                      botLink={botLink}
                    />
                  ))}
                </div>
              </div>
            );
          })}
      </div>
    </section>
  );
}
