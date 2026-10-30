# Implementazione locale CENA/DOPOCENA

Vedi [docs/complete-booking-system.md](docs/complete-booking-system.md) per le regole nuove e le dipendenze SQL. Nessuna migrazione, deploy o comunicazione reale è stata eseguita.

# Makai Grand Line — Sito ufficiale

Tiki Cocktail Bar & Ristorante a tema One Piece — Pigneto, Roma

## Stack tecnico

- **Frontend**: React 18 + Vite + Tailwind CSS 4
- **Gateway API**: funzione Node `api/backend-gateway.mjs` che inoltra `/api/*` al Backend Makai
- **Backend**: servizio FastAPI autonomo nel progetto `../backend-makai`
- **Database**: Supabase (PostgreSQL)
- **Deploy**: progetto Vercel del repository `sito-makai`, con frontend Vite e gateway Node; Makai Agenda è un'applicazione e repository distinti.

## Architettura dei progetti Makai

`sito-makai` (`lollomakai-alt/sito-makai`), `makai-agenda` (`lollomakai-alt/agenda-makai`) e `backend-makai` sono applicazioni autonome, ciascuna con il proprio repository e progetto Vercel. Condividono il progetto Supabase `fignmtkbwpbrmllbxoct` per database, autenticazione ADMIN e Edge Functions. Le regole di disponibilità e scrittura delle prenotazioni devono restare coerenti tra i progetti; verificali prima di cambiare tali regole.

Mappa operativa dei domini di produzione: `sito-makai` → `https://www.makaipigneto.it`; `makai-agenda` → `https://agenda-makai.vercel.app`. Conferma le associazioni correnti nelle impostazioni Domains dei rispettivi progetti Vercel: i file del repository non attestano la configurazione live.

Il flusso ordinario di rilascio Vercel è commit e push su GitHub nel repository corretto, che attiva il deploy automatico del progetto collegato. Non usare Vercel CLI per deploy manuali salvo richiesta esplicita. Non includere modifiche dell'altro progetto nel commit. Modifiche SQL o Edge Function su Supabase sono operazioni separate: verificare prima l'ambiente e non applicarle o distribuirle implicitamente.

Il Backend Makai (`../backend-makai`) salva direttamente su Supabase le prenotazioni online. Dopo il commit di una nuova prenotazione confermata chiama `web-push-admin` con `new-online-booking`; la chiave privilegiata resta lato server e un errore push non annulla il booking. Le notifiche operative mostrate nell’Agenda e le notifiche Web Push di sistema sono meccanismi distinti. La PWA Agenda può essere installata su iPhone; le subscription Apple Web Push sono conservate e gestite tramite Supabase. La consegna effettiva a un dispositivo dipende anche dalla subscription, dalle chiavi VAPID e dalla configurazione Edge Function.

## Struttura del repository

```
.
├── api/
│   └── backend-gateway.mjs # Gateway Node: inoltra /api/* al Backend Makai
├── src/                    # Frontend React
│   ├── components/         # Componenti UI (ChatWidget, HeroSection, HomeMenuSection, ecc.)
│   ├── pages/              # Pagine (MenuDetailPage, AboutPage, GalleryPage, Privacy.jsx)
│   ├── styles/             # CSS per sezione
│   ├── data/siteContent.js # Contenuto pagine menu (food/drink)
│   ├── hooks/              # Hook custom (usePageMotion)
│   └── sito.jsx            # Entry point Vite
├── public/images/          # Asset statici serviti da Vite
├── tests/                  # Test JavaScript
├── .env.example            # Variabili attese in produzione
├── vercel.json             # Configurazione Vercel (build + gateway)
└── package.json
```

## Sviluppo locale

Il Sito non contiene più il backend Python: è solo frontend + gateway. Per le API
avvia il progetto autonomo `../backend-makai`.

```bash
# Terminal 1: Backend Makai su :8000
cd ../backend-makai
UV_PROJECT_ENVIRONMENT=.venv-py312 uv sync --group dev
cp .env.example .env   # compila le variabili
UV_PROJECT_ENVIRONMENT=.venv-py312 uv run uvicorn app:app --host 127.0.0.1 --port 8000

# Terminal 2: Sito (Vite su :5173)
npm install
npm run dev
```

Il frontend usa il proxy Vite (`/api` → `http://127.0.0.1:8000`) definito in `vite.config.js`.
Per il Sito non serve un `.env` locale.

## Variabili d'ambiente

In produzione servono soltanto due variabili server-side. Fanno riferimento a
`.env.example`; la matrice completa dei tre progetti è in [`../AMBIENTI.md`](../AMBIENTI.md).

| Variabile | Valore |
| --- | --- |
| `API_PROXY_TARGET` | `https://backend-makai.vercel.app` (origine, senza `/api`) |
| `MAKAI_SITE_PROXY_SECRET` | almeno 32 caratteri, **identica** a quella del Backend |

Il Sito non usa più `DATABASE_URL`, `SUPABASE_*`, `ADMIN_*`,
`CHAT_SESSION_SECRET`, `MAKAI_PUSH_SECRET`, `ALLOWED_ORIGINS` né variabili
`VITE_*` proprie: appartengono al progetto Vercel `backend-makai` o a Supabase.
Non usare mai il prefisso `VITE_` per un segreto.

## Deploy su Vercel

`vercel.json` configura Vite in `dist/` e la funzione Node
`api/backend-gateway.mjs`: il browser chiama gli stessi URL `/api/*` e il gateway
li inoltra al Backend Makai. È distinto dal progetto Vercel del repository Agenda.

Il rilascio ordinario avviene con commit e push su GitHub in `sito-makai`; il progetto Vercel collegato dovrebbe avviare il deploy automatico. Verifica il collegamento Git e il dominio `www.makaipigneto.it` nella dashboard Vercel: i file locali non provano la configurazione live. Non usare Vercel CLI per deploy manuali salvo richiesta esplicita.

In **Settings → Environment Variables** del progetto imposta solo
`API_PROXY_TARGET` e `MAKAI_SITE_PROXY_SECRET`, poi esegui **Redeploy**. Entrambe
sono solo server-side: non inserirle in variabili `VITE_*`, nel browser o nel repository.

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
