# Implementazione locale CENA/DOPOCENA

Vedi [docs/complete-booking-system.md](docs/complete-booking-system.md) per le regole nuove e le dipendenze SQL. Nessuna migrazione, deploy o comunicazione reale è stata eseguita.

# Makai Grand Line — Sito ufficiale

Tiki Cocktail Bar & Ristorante a tema One Piece — Pigneto, Roma

## Stack tecnico

- **Frontend**: React 18 + Vite + Tailwind CSS 4
- **Backend**: FastAPI (Python 3.11) su Vercel Serverless Functions
- **Database**: Supabase (PostgreSQL)
- **Deploy**: progetto Vercel del repository `sito-makai`, con frontend Vite e API FastAPI; Makai Agenda è un'applicazione e repository distinti.

## Architettura dei progetti Makai

`sito-makai` (`lollomakai-alt/sito-makai`) e `makai-agenda` (`lollomakai-alt/agenda-makai`) sono applicazioni indipendenti, ciascuna con il proprio repository GitHub e progetto Vercel. Condividono il progetto Supabase `fignmtkbwpbrmllbxoct` per database, autenticazione ADMIN e Edge Functions. Le regole di disponibilità e scrittura delle prenotazioni devono restare coerenti nei due progetti; verifica entrambi i repository prima di cambiare tali regole.

Mappa operativa dei domini di produzione: `sito-makai` → `https://www.makaipigneto.it`; `makai-agenda` → `https://agenda-makai.vercel.app`. Conferma le associazioni correnti nelle impostazioni Domains dei rispettivi progetti Vercel: i file del repository non attestano la configurazione live.

Il flusso ordinario di rilascio Vercel è commit e push su GitHub nel repository corretto, che attiva il deploy automatico del progetto collegato. Non usare Vercel CLI per deploy manuali salvo richiesta esplicita. Non includere modifiche dell'altro progetto nel commit. Modifiche SQL o Edge Function su Supabase sono operazioni separate: verificare prima l'ambiente e non applicarle o distribuirle implicitamente.

Il backend di questo sito salva direttamente su Supabase le prenotazioni online. Dopo il commit di una nuova prenotazione confermata chiama `web-push-admin` con `new-online-booking`; la chiave privilegiata resta lato server e un errore push non annulla il booking. Le notifiche operative mostrate nell'Agenda e le notifiche Web Push di sistema sono meccanismi distinti. La PWA Agenda può essere installata su iPhone; le subscription Apple Web Push sono conservate e gestite tramite Supabase. La consegna effettiva a un dispositivo dipende anche dalla subscription, dalle chiavi VAPID e dalla configurazione Edge Function.

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

`vercel.json` configura un singolo progetto per questo repository: Vite compila il frontend in `dist/` e FastAPI è esposto dalle funzioni serverless in `api/`, con le rotte `/api/*`. È distinto dal progetto Vercel del repository Agenda.

Il rilascio ordinario avviene con commit e push su GitHub in `sito-makai`; il progetto Vercel collegato dovrebbe avviare il deploy automatico. Verifica il collegamento Git e il dominio `www.makaipigneto.it` nella dashboard Vercel: i file locali non provano la configurazione live. Non usare Vercel CLI per deploy manuali salvo richiesta esplicita.

In **Settings → Environment Variables** del progetto, aggiungi le variabili server-side:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `CHAT_SESSION_SECRET` (≥32 char)
   - `ADMIN_SESSION_SECRET` (≥32 char)
   - `ADMIN_PASSWORD` (password pannello admin)
   - `ADMIN_COOKIE_SECURE=true`
   - `ALLOWED_ORIGINS=https://tuo-dominio.vercel.app`

Le variabili privilegiate e le password devono restare solo nell'ambiente server; mai inserirle nelle variabili `VITE_*`, nel browser o nel repository.

## Funzionalità principali

- **Chatbot "Nostromo"** (`/api/chat`): menu, cocktail ed eventi; per prenotare indirizza alla pagina dedicata e non crea prenotazioni
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
