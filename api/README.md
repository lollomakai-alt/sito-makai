# Backend Makai e area gestore

Dalla cartella principale del progetto:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r api/requirements-dev.txt
.venv/bin/python -m uvicorn index:app --app-dir api --host 127.0.0.1 --port 8000
```

Avvia il sito con `npm run dev`, poi apri `/admin/login`.

## Indirizzi locali

Lascia frontend e backend in esecuzione in due terminali separati.
Il sito usa l'indirizzo stampato da Vite (normalmente `http://localhost:5173`).

| Indirizzo | Contenuto |
| --- | --- |
| `http://localhost:5173/` | Sito Makai |
| `http://localhost:5173/chi-siamo` | Chi siamo |
| `http://localhost:5173/galleria` | Galleria |
| `http://localhost:5173/menu-food` | Menu food |
| `http://localhost:5173/menu-drink` | Menu drink |
| `http://localhost:5173/admin/login` | Accesso gestore |
| `http://localhost:5173/admin/prenotazioni` | Calendario riservato |
| `http://127.0.0.1:8000/` | Stato del backend, come `/api/health` |
| `http://127.0.0.1:8000/docs` | Documentazione delle API |

Le pagine del sito vanno aperte sulla porta di Vite. La porta `8000` serve le API.
Vite inoltra le richieste `/api` al backend tramite il proxy in `vite.config.js`.
Per riavviare il backend, premi `Ctrl+C` nel suo terminale e ripeti il comando
Uvicorn riportato sopra dalla cartella principale del progetto.

## Account unico

Impostazioni nel `.env` principale (mai nel codice React):

- `ADMIN_USERNAME`: nome utente, predefinito `admin`.
- `ADMIN_PASSWORD`: password. Se assente, viene usata la precedente `ADMIN_API_KEY`.
- `ADMIN_SESSION_SECRET`: segreto casuale separato dalla password, almeno 32 caratteri.
- `ADMIN_COOKIE_SECURE`: `false` solo nello sviluppo locale HTTP; `true` in produzione HTTPS. Su Vercel è sempre attivo.

Le impostazioni si caricano all'avvio: dopo una modifica riavvia il backend.
In produzione imposta queste variabili nel servizio di hosting; il `.env` locale non viene pubblicato.
Il frontend e le API devono essere sullo stesso dominio, come con il proxy Vite e le route Vercel attuali.

## Accesso

- `/admin/login`: accesso con username e password.
- `/admin/prenotazioni`: agenda reale, con verifica della sessione.

Le API amministrative richiedono un cookie HttpOnly firmato, con durata massima di 8 ore e SameSite Strict. In produzione il cookie richiede HTTPS. La vecchia chiave nell'header `X-Admin-Key` non consente più l'accesso diretto alle API.
Le richieste POST usano `X-Admin-Request: 1` e controlli sull'origine. Il login limita i tentativi a 10 al minuto per processo; per un deployment con più istanze serve un limite condiviso o del provider.

Il logout rimuove il cookie dal browser. Le sessioni sono firmate e stateless: un'eventuale copia del cookie resta valida fino alla scadenza. Cambiare password o segreto invalida le sessioni precedenti dopo il riavvio di tutte le istanze.

Il login funziona anche senza database; l'agenda reale richiede `DATABASE_URL` e la tabella `bookings`.
La pulizia delle prenotazioni è disattivata per default. Impostare `BOOKINGS_AUTO_CLEANUP=true` abilita la cancellazione periodica dei record più vecchi di `RETENTION_DAYS`.

## Prenotazioni dalla chat

Scrivi `prenota` oppure `c'è posto per 4 sabato alle 21?` nella chat pubblica.
Il dialogo raccoglie persone, data, ora, nome, telefono, email e note, poi mostra
un riepilogo modificabile. Solo un sì esplicito salva la prenotazione confermata
nella tabella `bookings`, visibile nell'agenda del gestore.

Regole in `api/config.py`: lunedì chiuso, 18:00–23:00 (anche minuti intermedi),
anticipo minimo 30 minuti, massimo 60 giorni, da 1 a 6 persone, occupazione del
tavolo occupato per la giornata fino a liberazione esplicita e massimo 2 prenotazioni future per telefono. Il numero viene
normalizzato, così prefisso `+39`, `0039` e cellulare italiano senza prefisso non
aggirano il limite. Le alternative vengono proposte ogni 30 minuti.

`api/prenotazioni.py` gestisce conversazione e interpretazione di date/orari;
`api/bookings/service.py` verifica limiti e tavoli nella stessa transazione del
salvataggio. `annulla` interrompe solo la richiesta in corso. Per modificare o
cancellare prenotazioni già salvate il cliente contatta il locale.

Le sessioni usano un token firmato con scadenza dopo 30 minuti di inattività,
restituito da `/api/chat` e conservato solo nella memoria del componente React.
Funzionano tra processi diversi senza una tabella aggiuntiva. Imposta
`CHAT_SESSION_SECRET` (almeno 32 caratteri) oppure usa il già configurato
`ADMIN_SESSION_SECRET`: la firma della chat ha un salt distinto da quella admin.
Il token contiene dati della richiesta, è firmato ma non cifrato: non inserirlo
in URL, log o storage persistente; usa HTTPS in produzione. Ricaricare la pagina
azzera la conversazione nel browser. Se la risposta alla conferma si perde,
reinviare lo stesso sì con lo stesso token restituisce la prenotazione già salvata
anziché crearne un'altra (controllo dei dati e `created_at` sotto il lock esistente).

Il limite chat è 30 messaggi al minuto per IP e per processo. Non sostituisce un
limite condiviso del provider per deployment con più istanze.
Nessuna nuova tabella, dipendenza o autorizzazione Supabase è necessaria.
Non vengono inviati promemoria email; il campo `reminder_status` resta `skipped`.

## Verifica

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
npm run build
```

I test Python simulano il database e non inviano messaggi.

## Comprensione e memoria della chat

`automatic_chat.py` coordina lo stesso endpoint `/api/chat`, con risposta
`reply` e `session_token`. Non viene usato un servizio AI esterno: la comprensione
è locale, con sinonimi, refusi comuni, estrazione dei dati e contesto firmato.
Le frasi non riconosciute portano a una domanda di chiarimento, senza inventare risposte.

- `chat_language.py`: riconoscimento degli intenti e delle quantità, anche in lettere.
- `prenotazioni.py`: raccoglie più dati nella stessa frase e chiede solo quelli
  mancanti. Nome e cognome confluiscono nel campo `name` già esistente. Email
  e note restano nel flusso attuale: il servizio Bookings richiede un'email valida.
- `chat_menu.py`: legge soltanto `get_menu_data()`, quindi le righe disponibili
  del menu Supabase. I consigli citano prezzi e descrizioni reali; gli analcolici
  vengono filtrati nella loro categoria. Le caratteristiche mancanti non vengono dedotte.
- `chat_events.py`: pacchetti approvati dal locale, capienza e stime. Aperitivo
  €15, Apericena €25, tre pacchetti distinti dopo cena da €15; torta extra €3
  a persona, bottiglia di prosecco €20. Fino a 30 seduti, 31–40 in piedi con
  buffet, oltre 40 valutazione diretta. La chat registra soltanto le cene dalle
  18:00 alle 23:00. Il dopocena, disponibile dalle 22:30 alle 00:00, si prenota
  chiamando il locale; la chiusura è alle 02:00. Nessun evento viene salvato
  automaticamente.

Il token esistente conserva preferenze alimentari, argomento, preventivo e dati
prenotazione. Una domanda sul menu non sovrascrive nome o telefono. Passare agli
 eventi sospende il dialogo del tavolo: un successivo “sì” non salva una prenotazione.
Scrivere “riprendi prenotazione” recupera la bozza e richiede comunque la conferma
esplicita del riepilogo. Non ci sono variabili globali con memoria condivisa tra clienti.

Le possibilità di sushi vegetariano/senza glutine, poke vegetariane e modifiche
quando possibili sono indicazioni del locale, non garanzie sui singoli piatti.
Per allergeni e contaminazione la chat rimanda alla verifica con la struttura.
Non vengono creati tabelle, colonne o permessi nuovi; nessuna modifica al frontend.

`tests/test_automatic_chat.py` verifica gli esempi richiesti, i preventivi,
le sessioni isolate, i refusi e le interruzioni del dialogo con dati simulati.
`tests/test_booking_chat.py` continua a verificare conferma esplicita, errori,
limiti e idempotenza del servizio esistente. Nessun test inserisce record reali.
