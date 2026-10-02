import { useState } from 'react';
import { AuthProvider } from './context/AuthContext.jsx';
import { Navbar } from './components/Navbar.jsx';
import { Footer } from './components/Footer.jsx';
import { Home } from './pages/Home.jsx';
import { Products } from './pages/Products.jsx';
import { Balance } from './pages/Balance.jsx';
import { Orders } from './pages/Orders.jsx';
import { Profile } from './pages/Profile.jsx';

const SHOP_NAME = import.meta.env.VITE_SHOP_NAME || 'Gaming Shop';
const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || '';
const BOT_LINK = BOT_USERNAME ? `https://t.me/${BOT_USERNAME}` : null;

export default function App() {
  const [view, setView] = useState('home');
  const [productCategory, setProductCategory] = useState(null);

  function handleNavigate(nextView, category) {
    setView(nextView);
    if (nextView === 'products') setProductCategory(category || null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <AuthProvider>
      <div className="app">
        <Navbar shopName={SHOP_NAME} activeView={view} onNavigate={handleNavigate} />

        <main>
          {view === 'home' && <Home shopName={SHOP_NAME} onNavigate={handleNavigate} />}
          {view === 'products' && <Products initialCategory={productCategory} botLink={BOT_LINK} />}
          {view === 'balance' && <Balance botLink={BOT_LINK} />}
          {view === 'orders' && <Orders botLink={BOT_LINK} />}
          {view === 'profile' && <Profile botLink={BOT_LINK} />}
        </main>

        <Footer shopName={SHOP_NAME} botUsername={BOT_USERNAME} />
      </div>
    </AuthProvider>
  );
}
