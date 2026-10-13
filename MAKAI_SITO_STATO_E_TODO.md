# Sito Makai — Stato e attività
_13 ottobre 2026; Drive `ecosistema makai/sito makai`._

## Stato per livello di verifica (13 ottobre 2026)
- **DA FARE:** allineamento booking completo, verifiche mobile, comunicazioni, privacy, sicurezza e rilascio coordinato elencati sotto.
- **IMPLEMENTATO LOCALMENTE:** il documento `docs/complete-booking-system.md` e le modifiche locali esistenti descrivono lavoro presente nel checkout; in questo intervento non sono stati riesaminati né testati.
- **DEPLOYATO:** lo stato di deploy delle modifiche citate non è stato controllato in questo intervento.
- **VERIFICATO IN PRODUZIONE:** nessuna verifica di produzione svolta in questo intervento; le attività sopra non sono dichiarate completate.

## Migrazione SQL condivisa — 13 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** Agenda ha preparato `../makai-agenda/supabase/migrations/20261013170000_booking_engine_incremental.sql` per fornire al Sito `private.online_slot_status(day,slot,people,service,exclude_id)` e l'assegnazione CENA nello stesso INSERT. Nessuna API Sito o configurazione è stata modificata qui.
- **Verifiche:** lo schema live `public`/`private` è stato esportato in sola lettura con policy/GRANT e provato in PostgreSQL locale senza dati reali. Il percorso SQL online rispetta 25 persone per turno, incluse le manuali, e due connessioni concorrenti accettano un solo ultimo posto in CENA e DOPOCENA. Suite Python Sito 137/137 con `unittest`, JavaScript 6/6, build Vite e `git diff --check` superati.
- **DA FARE:** installazione autorizzata della sola migrazione incrementale e smoke test API Sito contro un ambiente aggiornato; il live continua a non esporre `private.online_slot_status`. La copia isolata non include dati reali né certifica le API distribuite.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** assenza della funzione riletta in sola lettura; nessuna nuova prenotazione live testata.

## Disponibilità online e quota DOPOCENA — verifica del 13 ottobre 2026
- **IMPLEMENTATO LOCALMENTE e verificato:** le API attuali `api/bookings/online.py` e `api/bookings/public_availability.py` interrogano `private.online_slot_status` con turno, orario e coperti. Il salvataggio online usa la stessa transazione del controllo SQL e dell'INSERT; il trigger Agenda proposto ripete il controllo sotto lock 734512. Aggiunti test che dimostrano il blocco senza INSERT e senza disponibilità inventata quando la funzione SQL manca; aggiornato un test ADMIN che trattava slot e date manuali come vincoli online. La suite Python completa passa **136/136**; la suite JavaScript **6/6**, la build Vite e `git diff --check` riescono. Nessun cambiamento alla logica API o alla UI in questo intervento.
- **DA FARE:** nell'ultimo inventario live di sola lettura `private.online_slot_status` risultava assente; la migrazione completa Agenda resta soltanto preparata, anche se la migrazione del catalogo tavoli è già applicata. Verificare planner online, quota automatica di 25 per entrambi i turni separati, transazioni simultanee, errori API e percorso iPhone prima di un rilascio. Non usare fallback alla vecchia `online_day_status`, che applica regole di conteggio differenti. Nessun SQL applicato qui.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** solo presenza/assenza della funzione nello schema letta; nessuna prenotazione o API live testata. Nessun commit, push o deploy.

## Catalogo tavoli e quote per turno — allineamento locale, 13 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** il Sito continua a delegare disponibilità e assegnazione tavoli al catalogo/planner SQL condiviso; non è stata aggiunta una copia locale del catalogo. Il contratto SQL è allineato alla migrazione già applicata `table_group_13_14_3_and_22_23_4`: 13+14=3 fisso, 22 e 23 singoli da 2, gruppo 22+23=4 selezionabile anche dal planner automatico se compatibile e libero.
- La capienza fisica standard CENA è 26; la quota automatica è 25 persone per ciascun turno e i conteggi CENA/DOPOCENA restano separati. Le API Sito passano tipo di servizio e slot a `private.online_slot_status`; non applicano capienze tavolo localmente.
- **Verifiche (13 ottobre 2026):** il test mirato di disponibilità passa (5/5); suite Python completa 137/137, suite JavaScript 6/6 e build Vite passano. Il test conferma che per DOPOCENA il Sito inoltra `booking_type='dopocena'` e slot 22:30 alla funzione condivisa, senza duplicare il catalogo né il calcolo delle capienze. `git diff --check` superato. Nessuna modifica al database live.
- **DA FARE:** verificare che la funzione `private.online_slot_status` sia presente e aggiornata nello schema live e provare le quote con database isolato prima del rilascio.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** non verificato in questo intervento; la dichiarazione della migrazione già applicata è separata dalla verifica del planner e delle API live.

## Registro intervento documentale — 13 ottobre 2026
- Aggiunto `AGENTS.md` con letture obbligatorie e collegamenti relativi ai documenti Sito ed ecosistema.
- Verificata la presenza dei documenti e delle istruzioni; codice, database e produzione non toccati.

## Registro — preparazione commit e push, 14 ottobre 2026
- **Perimetro:** inventario delle modifiche locali, controllo dei file candidati per segreti e dei meccanismi di pubblicazione, verifiche locali. Il codice applicativo, SQL e database non sono stati modificati in questo intervento.
- **IMPLEMENTATO LOCALMENTE:** il checkout contiene il lavoro descritto sopra; il presente intervento ne prepara il versionamento su un branch dedicato. La cartella generata `.engram ` resta esclusa dal commit. Il nuovo backend online richiede ancora la funzione SQL condivisa `private.online_slot_status`, indicata come non applicata nel documento Agenda.
- **Verifiche del 14 ottobre:** suite Python 137/137, suite JavaScript 6/6, `npm run build` superata (Vite 8.3.0, 50 moduli), `git diff --check` superato. Scansione dei file modificati senza credenziali individuate; il valore `SERVICE_KEY` in un test è una fixture. Nessun controllo browser, staging o database in questo intervento.
- **DA FARE:** chiarire il collegamento Git/Vercel prima di inviare il branch remoto: in assenza di una disabilitazione verificata, il push potrebbe creare automaticamente un deploy Preview. Coordinare qualsiasi futura pubblicazione con la migrazione SQL Agenda ancora non applicata.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun push o deploy in questo intervento.

## Architettura
- React + Vite + Tailwind; backend FastAPI; Supabase PostgreSQL e Vercel.
- Progetto distinto da Agenda ma regole booking condivise. UI cliente mobile-first.
- Sul Drive risultano `src`, `api`, `tests`, `docs`, `supabase`, `public`, README, config.

## Flusso aggiornato documentato (12/10)
- CENA 19:00–22:30, DOPOCENA 22:30–00:00, selezione esperienza.
- Disponibilità online basata sul planner SQL; CENA con tavolo assegnato automaticamente; DOPOCENA senza tavolo, quota 25 distinta.
- Orari non disponibili visibili ma disabilitati; ricontrollo lato server alla conferma.
- Token sicuro in fragment `#token=…` per gestione richiesta e riconferma; approvazione manuale delle modifiche/cancellazioni.
- Conferme/email tramite Edge/Resend; script `booking_reminders.py` non pianificato e in lettura per default.

## Da verificare / implementare
1. **Rilascio nuovo booking:** il documento `docs/complete-booking-system.md` dice espressamente non pubblicato; allineare migrazione SQL + backend + frontend.
2. **Test mobile-first:** iPhone reale, slot disabilitati, mezzanotte corretta, messaggi disponibili/non disponibili, form e privacy.
3. **Comunicazioni:** scheduler giorno prima, recapiti, template Makai, gestione fallimenti e link sicuri.
4. **Privacy:** informativa aggiornata, consenso marketing separato e facoltativo, conservazione/trasferimenti e segnaposto legali da completare.
5. **Sicurezza:** rate limiting, sessioni, CORS, chiavi server, controllo idempotenza e conflitti contemporanei.
6. **Allineamento documentazione:** README ha introduzione nuova ma sezioni storiche con vecchi orari 18–23 e prenotazione online senza tavolo; marcare esplicitamente deprecated.
7. **Test e rilascio:** suite frontend/backend e due connessioni PostgreSQL; staging, poi distribuzione coordinata con Agenda.

## Fonti Drive
- https://drive.google.com/file/d/19APj-hR-XsU6QonQanJ_TajV7WLsGvDb/view
- https://drive.google.com/file/d/1oMakcbTqQeDhb5Kn2M0SyGNpIHS4KkGN/view
- https://drive.google.com/file/d/1MWnObx2jP8p1AZkeO5z91o88INUISu4k/view
