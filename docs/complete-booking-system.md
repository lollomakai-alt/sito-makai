# CENA e DOPOCENA — stato locale 12 ottobre 2026

Il sito usa `private.online_slot_status` e il planner SQL condiviso nell’Agenda; non mantiene un catalogo tavoli duplicato nel codice FastAPI/frontend. Il catalogo Supabase della migrazione già applicata `table_group_13_14_3_and_22_23_4` è la fonte condivisa: 13+14 fisso da 3; 22 e 23 separati da 2 oppure 22+23 da 4, anche candidato automatico se compatibile e libero. La capienza fisica standard CENA è 26; la quota automatica è 25 persone per turno, separata tra CENA e DOPOCENA. CENA viene assegnata automaticamente; DOPOCENA nasce senza tavolo.

Le regole definitive, i prerequisiti SQL e le verifiche di rilascio sono in `../makai-agenda/docs/complete-booking-system.md`. La migrazione finale è `../makai-agenda/supabase/complete-booking-system.sql`: va applicata dopo i prerequisiti, mai durante i test. I due repository restano separati; non importano codice l’uno dall’altro.

Il cliente riceve un link casuale per `/prenotazioni/gestisci#token=…`; token validati solo sul backend, hash nella tabella privata, nessun booking_id pubblico. Le richieste di modifica/cancellazione attendono l’approvazione staff e conservano lo stesso record. La riconferma non annulla mai automaticamente la prenotazione.

Conferme e reminder riutilizzano l’Edge `send-booking-email` e Resend. `scripts/booking_reminders.py` non scrive né invia per default; `--prepare` accoda, `--send` invia solo mediante claim/log esistenti. Non è stata configurata alcuna schedulazione. `PUBLIC_SITE_URL` deve essere l’origine HTTPS del sito; il default è https://www.makaipigneto.it.

Prima della pubblicazione verificare schema live, Auth/RLS, inviti/redirect, Realtime, concorrenza a due connessioni, Safari/iPhone e informative aggiornate. Serve un rilascio coordinato di SQL, backend, Edge email e due frontend. Nessuna modifica live o comunicazione reale è stata effettuata.

Verifiche locali: `.venv/bin/python -m unittest discover -s tests`, `npm run test:js`, `npm run build`, `git diff --check`. I test API simulano trasporto e database; il SQL effettivo è testato in PGlite nel repository Agenda.
