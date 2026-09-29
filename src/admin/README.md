# Gestione interna Makai

Quest'area frontend è autonoma rispetto alla grafica del sito pubblico.
`src/main.jsx` carica `AdminApp.jsx` solo per gli indirizzi `/admin` e `/admin/*`.
Gli stili, le immagini e le animazioni del sito pubblico non vengono caricati in quest'area.

- `AdminApp.jsx`: ingresso e percorsi dell'area amministrativa.
- `pages/LoginPage.jsx`: login.
- `pages/CalendarPage.jsx`: mese corrente, navigazione e coperti per giorno.
- `pages/BookingsPage.jsx`: giornata selezionata e pulsante WhatsApp.
- `components/AdminAccess.jsx`: verifica della sessione.
- `components/LogoutButton.jsx`: uscita dall’area riservata.
- `styles/admin.css`: tutti gli stili della gestione interna.
- `utils/bookingConfirmation.js`: testo e link WhatsApp.
- `utils/calendar.js`: date, griglia lunedì–domenica e navigazione mensile.

Indirizzi: `/admin/login`, `/admin/prenotazioni` (mese corrente),
`/admin/prenotazioni?month=AAAA-MM` e `/admin/prenotazioni/giorno?date=AAAA-MM-GG`.
Il ritorno dal giorno conserva il mese selezionato. I coperti includono solo le prenotazioni confermate.
Il backend resta nella cartella `api/` e verifica la sessione sulle API dell'agenda.
