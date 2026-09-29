import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

async function startApp() {
  const path = window.location.pathname;
  const isAdmin = path === '/admin' || path.startsWith('/admin/');
  // Carica solo l'app e gli stili dell'area richiesta.
  const { default: App } = isAdmin
    ? await import('./admin/AdminApp.jsx')
    : await import('./app.jsx');

  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

startApp();
