# Makai Grand Line — Sito ufficiale

Tiki Cocktail Bar & Ristorante a tema One Piece — Pigneto, Roma

## Stack tecnico

- **Frontend**: React 18 + Vite + Tailwind CSS 4
- **Backend**: FastAPI (Python 3.11) su Vercel Serverless Functions
- **Database**: Supabase (PostgreSQL)
- **Deploy**: Vercel (monorepo con **services**: `app` + `api`)

## Struttura del repository

```
.
├── api/                    # Backend FastAPI
│   ├── index.py           # Entry point (esporta `app = FastAPI(...)`)
│   ├── automatic_chat.py  # Logica chatbot Nostromo
│   ├── chat_menu.py       # Risposte su menu/cocktail
│   ├── chat_events.py     # Gestione eventi/feste
│   ├── prenotazioni.py    # Flusso prenotazioni
│   ├── bookings/          # Moduli agenda (service, dates, tables, validators)
│   ├── menu_data.py       # Fetch menu da Supabase
│   ├── admin_auth.py      # Auth pannello admin (cookie session)
│   ├── config.py          # Costanti configurabili via env
│   └── requirements.txt   # Dipendenze Python
├── src/                   # Frontend React
│   ├── components/        # Componenti UI (ChatWidget, HeroSection, HomeMenuSection, ecc.)
│   ├── pages/             # Pagine (MenuDetailPage, AboutPage, GalleryPage, Privacy.jsx)
│   ├── styles/            # CSS per sezione
│   ├── data/siteContent.js# Contenuto pagine menu (food/drink)
│   ├── hooks/             # Hook custom (usePageMotion)
│   └── sito.jsx           # Entry point Vite
├── public/images/         # Asset statici serviti da Vite
├── vercel.json            # Configurazione Vercel Services
└── package.json
```

## Sviluppo locale

```bash
# Terminal 1: Backend (FastAPI su :8000)
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # compila le variabili
uvicorn index:app --reload --port 8000

# Terminal 2: Frontend (Vite su :5173)
npm install
npm run dev
```

Il frontend usa il proxy Vite (`/api` → `http://127.0.0.1:8000`) definito in `vite.config.js`.

## Variabili d'ambiente

Crea un file `.env` nella root (non committato) basandoti su `.env.example`:

```env
# Frontend (Vite)
VITE_API_URL=http://localhost:8000/api

# Backend (FastAPI)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxx
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxxx
CHAT_SESSION_SECRET=almeno-32-caratteri-casuali
ADMIN_SESSION_SECRET=almeno-32-caratteri-casuali
ADMIN_PASSWORD=la-tua-password-admin
ADMIN_COOKIE_SECURE=false
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
BOOKINGS_AUTO_CLEANUP=false
```

## Deploy su Vercel

Il repo è configurato come **Vercel Project con due Services** (`vercel.json`):

| Servizio | Framework | Root | Pubblico su |
|---|---|---|---|
| `app` | Vite (React) | `.` | `/` (SPA catch-all) |
| `api` | FastAPI | `api/` | `/api/*` (via rewrite) |

### Passaggi deploy

1. Importa il repository GitHub su Vercel → "Add Project"
2. Vercel rileva automaticamente `vercel.json` e crea i due servizi
3. In **Settings → Environment Variables** del progetto, aggiungi le variabili per il servizio `api`:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `CHAT_SESSION_SECRET` (≥32 char)
   - `ADMIN_SESSION_SECRET` (≥32 char)
   - `ADMIN_PASSWORD` (password pannello admin)
   - `ADMIN_COOKIE_SECURE=true`
   - `ALLOWED_ORIGINS=https://tuo-dominio.vercel.app`
4. Deploy! Il frontend builda in `dist/`, l'API gira come serverless function.

## Funzionalità principali

- **Chatbot "Nostromo"** (`/api/chat`): menu, cocktail, eventi, prenotazioni conversazionali
- **Prenotazioni** con disponibilità real-time, limite 6 persone online, consenso privacy opzionale (`consenso_ricordami`)
- **Pagine Menu** (`/menu-food`, `/menu-drink`) con dati live da Supabase
- **Agenda separata**: progetto autonomo `../makai-agenda`, avvio con `npm run dev` su http://localhost:5174. Il backend condiviso espone ancora le API protette `/api/admin/*`.
- **Privacy page** (`/privacy`) linkata dalla chat
- **Gallery**, **Chi siamo**, **Contatti**, **Eventi**

## Script utili

```bash
npm run dev       # Avvia Vite dev server
npm run build     # Build produzione in dist/
npm run preview   # Anteprima build locale
```

## Licenza

Progetto privato — Makai Grand Line Pigneto.

## Agenda indipendente

Il sito pubblico monta soltanto `src/app.jsx`. Il frontend dell’agenda è stato spostato in `../makai-agenda`, con package.json, stili, configurazione e test propri. Nessun file del sito importa quel progetto.

Le API in `api/` restano condivise tra chat cliente e agenda: l’estrazione non cambia database, credenziali o regole di prenotazione. Il vecchio percorso frontend `/admin/login` non è più il login dell’agenda.
