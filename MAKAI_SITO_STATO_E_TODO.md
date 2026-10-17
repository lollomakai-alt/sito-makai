# Sito Makai — Stato e attività
## Push Sito e Backend, Agenda esclusa — 17 ottobre 2026
- **DEPLOYATO:** commit applicativo Sito `b0751c8a25b11ccaac41e60fb44713169075e5b6` inviato a `origin/main`; Vercel deployment `dpl_6R7H4t9i6VyB1k12N7wdmGAUohKc` READY e associato a `www.makaipigneto.it`, `sito-makai.vercel.app`, `prenota.makaipigneto.it` e dominio principale. Backend `f74d212` anch'esso inviato e READY sul dominio stabile. Il successivo aggiornamento di questo registro non cambia il codice applicativo.
- **Contenuto:** gateway autonomo, feedback moduli, pagina gestione prenotazioni responsive, titoli condivisi e privacy IT/EN (`src/pages/Privacy.jsx`, inclusi 30 giorni operativi/12 mesi marketing e DPO). I 50 file legacy rimossi corrispondono esattamente al backup SHA-256 `112d5e6a689df2e1b0e6aaab211d0386e3c3c3805a0b8118bd77a6580f7c51f2`; il gateway Node era già pubblicato prima di questo push. File ambiente e cartella locale `.engram ` esclusi.
- **Verifiche:** test/build locali riportati sotto; nuovo deployment e alias confermati via CLI Vercel dopo errore 403 del connettore. HTTP pubblico verificato separatamente, senza inviare moduli o usare token cliente. Nessuna verifica visiva iPhone o UI autenticata dichiarata.
- **VERIFICATO IN PRODUZIONE (HTTP/artefatto):** `/api/health`, `/api/site-maintenance`, `/privacy` e `/prenotazioni/gestisci` HTTP 200; `/api/admin/session` HTTP 404 tramite gateway pubblico. Il CSS servito dal dominio contiene il nuovo stile condiviso `site-heading`. La pagina gestione è stata aperta senza token: non prova un flusso cliente completo.
- **DA FARE:** Agenda resta interamente locale su richiesta dell'utente. La migrazione delle scadenze dei 33 contatti preesistenti non è stata applicata; il push aggiorna codice/nuovi consensi, non corregge quei record. Nessuna funzione Edge, migrazione SQL o email pubblicata/inviata in questo intervento. L'allineamento Production complessivo resta parziale.

## Allineamento verificato con Backend e Agenda — 17 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** testi privacy e codice consenso restano allineati a 30 giorni operativi e 12 mesi marketing. Per gli storici già convertiti in prenotazione il Backend segue ora la data effettiva del servizio, come precisato dall'utente; il contatto marketing conserva il ciclo separato dopo lo scollegamento FK della prenotazione scaduta.
- **Verifiche correnti:** Sito JavaScript 17/17 e build Vite 57 moduli; gateway Backend 9/9; Backend Python 150 + 37 subtest; Agenda 263/263, email 12 passaggi e build. PostgreSQL temporaneo con dati sintetici: funzioni reali di consenso Sito/Agenda, rinnovo/revoca, migrazione 12 mesi, cleanup con tutte le FK pertinenti, rischedulazioni e rollback su errore superati.
- **Limiti:** nessuna prova browser/iPhone, invio reale o ciclo serverless schedulato in questo intervento; nessun clone completo di Supabase/staging. Solo aggregati e metadati live letti: 33 scadenze marketing da anticipare e nessuna che diventerebbe già scaduta. **DA FARE:** migrazione autorizzata e rilascio coordinato Backend/Sito/Agenda, quindi prenotazione controllata e verifica consegna email. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no per le modifiche locali. Nessun commit/push/deploy, scrittura dati o invio.

## Conservazione dati: 30 giorni operativi e 12 mesi marketing — 17 ottobre 2026
- **Decisione utente:** dati operativi legati al servizio per 30 giorni; consenso marketing e prova del consenso per un massimo di 12 mesi, uso promozionale sospeso subito in caso di revoca.
- **IMPLEMENTATO LOCALMENTE:** informativa italiana e inglese aggiornata per descrivere le scadenze operative e marketing; SQL base `supabase/marketing_contacts_retention.sql` allineato a 12 mesi. Il Backend condiviso imposta la stessa scadenza per i consensi acquisiti dal Sito.
- **Verifiche:** JavaScript 17/17 e build Vite completata (57 moduli); `git diff --check` superato. Nessun browser/iPhone controllato.
- **DA FARE:** pubblicazione coordinata dopo prova integrata cleanup e revisione della migrazione Supabase. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no; nessuna configurazione/database modificati.

## Controllo preparazione push — 17 ottobre 2026
- **Repository:** branch `main` allineato al commit remoto (`origin/main`), ma working tree contiene 72 percorsi modificati/in aggiunta/rimozione. Le cancellazioni dei moduli API e test backend fanno parte del passaggio al Backend autonomo già documentato; non sono state ripristinate.
- **Verifiche locali:** test JavaScript 17/17 superati; build Vite superata su `/tmp/makai-sito-build` (57 moduli). La build standard nella cartella `dist` è stata impedita da permessi su `dist/.DS_Store`; la variante temporanea ha evitato di modificare tale cartella. `git diff --check` superato.
- **DEPLOYATO / push:** nessun commit o push eseguito in questa verifica.
- **Vercel:** il repository mappa il progetto `sito-makai`, ma l'ispezione del progetto e dei deploy è stata negata per scope 403; il CLI ha restituito `fetch failed`. Non è quindi confermato se `main` avvii automaticamente un deploy Production. **DA FARE:** ripristinare accesso Vercel e verificare il collegamento Git, branch Production e progetto prima del push.

## Audit informativa privacy rispetto ai flussi effettivi — 17 ottobre 2026
- **Aggiornamento locale:** l'informativa italiana e inglese ora descrive chat temporanea, lista d'attesa, log delle comunicazioni, IP per limitazione abusi, preferenza lingua, link esterni e uso facoltativo di WhatsApp. Rimossa l'affermazione “12 mesi con consenso a essere ricordati”, non supportata dai moduli attuali. Il testo indica Alessio Esposito quale DPO/RPD nominato e `makairoma@gmail.com` quale recapito, come comunicato dall'utente.
- **Conservazione:** l'utente conferma che la pulizia automatica Production è attiva e impostata a 30 giorni; non è stata letta la variabile runtime. La lettura read-only dei vincoli FK Production ha rilevato relazioni `RESTRICT`/`NO ACTION` da richieste DOPOCENA, richieste prenotazione e lista d'attesa alle prenotazioni: una cancellazione bloccata può far fallire l'operazione di pulizia. L'informativa ora rende esplicito questo limite. I periodi separati per richieste, liste, storico, ricevute e log devono ancora essere verificati e definiti.
- **Metadati Production verificati:** presenti tabelle personali per prenotazioni, richieste DOPOCENA, richieste/storico, comunicazioni/log provider, token cliente, ricevute di idempotenza, contatti marketing, lista d'attesa e storico lista. La tabella prenotazioni e le principali tabelle elencate hanno RLS attiva; questo non prova da solo la correttezza delle policy o i tempi di cancellazione.
- **DA FARE:** verificare e correggere il cleanup in presenza delle relazioni FK; verificare i tempi effettivi per ciascuna classe di storico; convalidare basi giuridiche, canali marketing e nomine/DPA con il titolare/DPO. **IMPLEMENTATO LOCALMENTE:** aggiornato il testo IT/EN e questa nota di stato; modifica locale non pubblicata. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** sola lettura di metadati schema e vincoli FK; attivazione cleanup riferita dall'utente, non verificata autonomamente. Nessuna riga personale letta, nessun DB o runtime modificato. `git diff --check` superato; build Vite tentata ma bloccata da `EPERM` in `node_modules/.vite-temp`; nessun controllo browser eseguito.

## Campi pagina gestione prenotazione più stabili su iPhone — 17 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** i controlli della scheda raggiunta dal link email hanno larghezza massima vincolata al contenitore, larghezza minima azzerata e carattere da 16 px per evitare l'ingrandimento automatico al focus in Safari iOS. Il form dispone ora i campi con spaziatura regolare; i testi lunghi possono andare a capo.
- **Perimetro:** regole limitate a `.customer-manage-form`; nessuna modifica alla logica di riconferma, richiesta modifica o cancellazione.
- **Verifiche e limiti:** controllo CSS statico e `git diff --check`; non effettuato un test su iPhone o simulatore, né una build in questo intervento. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no.

## Schermata manutenzione esclusa nell'ambiente locale — 17 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** in sviluppo (`import.meta.env.DEV`) il Sito non interroga l'endpoint remoto `/api/site-maintenance` e non sostituisce le pagine con la schermata di manutenzione. Le rotte locali, inclusa `/prenotazioni`, restano accessibili anche se il backend locale non è avviato.
- **Perimetro e protezioni:** la verifica e il blocco manutenzione restano attivi nelle build non di sviluppo; nessuna configurazione o risorsa di produzione è stata modificata. Il componente della schermata resta disponibile per l'ambiente online.
- **Verifiche e limiti:** controllo del flusso in `src/app.jsx` e `git diff --check`; nessun controllo browser, build, deploy o verifica in produzione eseguiti in questo intervento. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no.

## Titoli principali uniformati — 17 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** introdotto `SiteHeading` come componente e stile condiviso per i titoli principali del Sito. Hero, Chi siamo, Menu, Eventi, Contatti, pagine About/Menu/Galleria, Prenotazione (“Un posto per te”), gestione prenotazione, Privacy e Manutenzione usano ora la stessa tipografia pirata dorata e lo stesso divisore con teschio; l’Hero conserva una variante di dimensione. Titoli interni a schede, categorie e passaggi del modulo restano gerarchicamente secondari.
- **Perimetro:** solo componenti di intestazione e CSS associato; testi, moduli, navigazione e comportamenti invariati. Modifiche locali preesistenti preservate.
- **Verifiche e limiti:** revisione statica dei riferimenti JSX/CSS; nessun test, build o controllo visivo browser/dispositivo eseguito. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.

## Pagina gestione prenotazione collegata alla mail di riconferma — 17 ottobre 2026
- **IMPLEMENTATO LOCALMENTE (presenza verificata):** la route `/prenotazioni/gestisci` e la pagina unica esistono già nel codice. La pagina usa il token personale dal fragment e presenta riconferma, richiesta di modifica e annullamento per prenotazioni confermate; le regole applicative restano quelle del Backend condiviso.
- **Verifica collegamento:** il preparatore di template Agenda crea un token e passa l’URL assoluto al template `reconfirmation`; il testo email ora descrive esplicitamente riconferma, modifica e annullamento.
- **Verifiche e limiti:** build Sito Vite superata (56 moduli), compresa la pagina di gestione; il link personale non è stato aperto con un token valido e non è stata inviata un’email. La route pubblica era stata raggiunta senza token in una verifica precedente, che non certifica l’intero flusso.
- **DEPLOYATO:** nessuna modifica in questo intervento. **VERIFICATO IN PRODUZIONE:** no per l’email e il flusso con token valido. Nessun commit, push o deploy.

## Backend autonomo attivato — 16 ottobre 2026
- **DEPLOYATO:** gateway Node Sito `dpl_HWeyTSoKwE6mE6L6vBxMnnNmPEEB` promosso su Production, con target `https://backend-makai.vercel.app` e segreto gateway configurato in Vercel.
- **VERIFICATO IN PRODUZIONE:** sul dominio Sito HTTP 200 per health, manutenzione, impostazioni e disponibilità; manutenzione `false`. Menu HTTP 200 sulla candidata prima della promozione. Il gateway blocca `/api/admin/session` con 404. `POST /api/bookings` con body vuoto restituisce 422 prima di una scrittura. La prenotazione di prova riferita dall'utente precedeva questo deployment e non verifica la nuova scrittura.
- **IMPLEMENTATO LOCALMENTE:** sostituita la vecchia funzione Python con `api/backend-gateway.mjs`, aggiornato `vercel.json` alla rotta Node e aggiunto `.vercelignore`. Rimossi dal checkout i 50 file legacy API/test/script; archivio e manifesto verificati, SHA-256 archivio `112d5e6a689df2e1b0e6aaab211d0386e3c3c3805a0b8118bd77a6580f7c51f2`.
- **DA FARE:** inviare una prenotazione controllata dopo il cutover e confermarne la comparsa in Agenda; annullarla da Agenda se usata come test. Nessun commit o push in questo intervento; le modifiche restano locali oltre al deployment manuale già promosso.

## Preparazione al Backend autonomo — fotografia precedente al cutover Sito
- In questa fotografia il pacchetto Sito era pronto ma non ancora pubblicato e i sorgenti del checkout erano ancora presenti.
- Il Backend autonomo era stato pubblicato; Sito live usava ancora la funzione Python. La fotografia è superata dal cutover descritto nella sezione più recente sopra.

_13 ottobre 2026; Drive `ecosistema makai/sito makai`._

## Preparazione separazione Backend — fotografia storica del 15 ottobre 2026
- **Obiettivo corrente:** estrarre il backend in un progetto Vercel indipendente condiviso da Sito e Agenda. Il precedente mantenimento definitivo del backend nel Sito era un'interpretazione non corrispondente alla richiesta dell'utente.
- **IMPLEMENTATO LOCALMENTE:** i 50 file aggiornati API/test Python/script sono stati copiati e verificati nel nuovo `../backend-makai`, con entrypoint e configurazione indipendenti; 149 test Python e 6 test del futuro proxy superati. Il Sito conserverà frontend e inoltro pubblico `/api/*`, preparato in `../backend-makai/integration/site/`; Agenda manterrà il proprio gateway ADMIN.
- **Limite corrente:** nessun sorgente originale del Sito è stato rimosso o modificato; il manifesto SHA-256 ne verifica l'integrità. La rimozione anticipata è stata respinta dalla revisione automatica: il passaggio finale attende verifica del servizio autonomo e autorizzazione coordinata.
- **DEPLOYATO:** no per questa architettura; nessun nuovo progetto remoto, commit, push o deploy. **VERIFICATO IN PRODUZIONE:** no per Backend autonomo/proxy. Nessuna modifica a Supabase o alle configurazioni online.
- **DA FARE:** pubblicare prima il Backend autonomo, aggiornare il target Agenda, poi attivare il proxy Sito e ritirare gli originali dopo verifica e backup. Documentazione di passaggio nel progetto Backend; gli altri rilievi dell'audit restano attività distinte.

## Sorgente unica del backend — fotografia storica del 15 ottobre, superata il 16 ottobre
- **IMPLEMENTATO LOCALMENTE:** confermata `sito-makai/api` come sorgente del backend condiviso. Rimossa, su richiesta esplicita dell'utente, la copia indipendente `../backend-makai` dopo archivio recuperabile e verifica SHA-256 di tutti i 54 file. Il contenuto di `api/` è identico prima/dopo; nessuna sincronizzazione dei file vecchi sopra il Sito.
- **Documentazione:** stato Backend preservato in `../MAKAI_BACKEND_STATO_E_TODO.md`; lettura aggiunta ad `AGENTS.md` senza rimuovere le istruzioni esistenti. Roadmap comune aggiornata. Le correzioni individuate dall'audit del Backend restano da fare.
- **Evidenze:** `vercel.json` pubblica `api/index.py` dal repository Sito; stato Vercel `success` per il commit preesistente `e233f74c02e2f5da37433345076038975df09e06`. Il target effettivo nel `.env` locale Agenda punta a `sito-makai.vercel.app`. Nessun server Python/Uvicorn rilevato sulla copia separata e nessun listener locale sulla porta 8000.
- **VERIFICATO IN PRODUZIONE:** soltanto GET HTTP 200 di `/api/health` e `/api/site-maintenance` su `sito-makai.vercel.app` e `www.makaipigneto.it`. Nessuna sessione ADMIN o variabile Vercel dell'Agenda ispezionata. **DEPLOYATO:** nessun nuovo rilascio, commit o push in questo intervento; nessun SQL o configurazione Supabase modificati.
- **DA FARE:** usare questa sorgente unica per le correzioni successive del backend e completare le verifiche funzionali già documentate. Archivio e manifesto di recupero sono indicati nel documento Backend comune.

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

## Registro — manutenzione temporanea del Sito, 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** pagina Makai responsive con logo e contatti già presenti nel progetto; controllo globale tramite `GET /api/site-maintenance` senza cache e aggiornamento periodico. Se lo stato non è leggibile, il Sito mostra la pagina di manutenzione. La privacy e la gestione delle prenotazioni esistenti restano accessibili.
- **IMPLEMENTATO LOCALMENTE:** il backend controlla `private.site_maintenance` nella stessa transazione con lock della nuova prenotazione online; anche l'API di disponibilità pubblica non annuncia posti durante la manutenzione. Le API amministrative Agenda leggono e modificano lo stato solo con ruolo `admin`, gateway autorizzato e protezione dell'azione browser. Ogni cambio effettivo viene registrato in `private.site_maintenance_history`; nessuna prenotazione esistente viene modificata.
- **SQL preparato separatamente:** `supabase/site-maintenance.sql` crea il singleton di stato e lo storico privato con RLS e privilegi revocati ai client pubblici. Non è stato applicato. La CLI Supabase non era disponibile localmente, quindi il file è una proposta SQL separata e non una migrazione numerata generata dalla CLI.
- **Verifiche locali:** suite Python 142/142, JavaScript 9/9 e build Vite (53 moduli) superate. Browser locale: pagina verificata a 390×844 e 1280×800; a 390 px larghezza documento 390 px e collegamenti di contatto alti 48 px. Il backend locale non era configurato, perciò il browser ha verificato il comportamento di blocco per stato non disponibile. Nessun test autenticato end-to-end o su iPhone fisico.
- **DA FARE prima dell'uso:** revisionare e applicare separatamente lo SQL in una finestra autorizzata; pubblicare insieme backend/Sito e controllo Agenda; verificare lettura iniziale `active=false`, autorizzazioni amministrative e blocco delle API pubbliche su staging. Per attivare: entrare in Agenda come admin, aprire **Manutenzione sito**, premere **Attiva manutenzione** e verificare lo stato letto dal server. Per disattivare: dalla stessa pagina premere **Disattiva manutenzione** e verificare il nuovo stato. Questi comandi non richiedono un ulteriore deploy dopo l'installazione iniziale.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push, deploy o intervento sul database live in questo intervento.

## Verifica permessi manutenzione, 14 ottobre 2026
- **Verifica locale/isolate:** `site-maintenance.sql` installato su PGlite temporaneo con ruoli `anon`, `authenticated`, `service_role` e schema `private`; stato iniziale `false`, transizioni `true` e `false` e due righe storico riuscite; `service_role` non può leggere le tabelle. Nessun dato reale o connessione Supabase.
- Il backend apre `DATABASE_URL` con psycopg; il file `.env` locale indica un utente di connessione con prefisso `postgres`. Tale ruolo è proprietario/superuser atteso per la creazione da SQL Editor/migrazione, quindi le query private funzionano senza concedere accesso al client `service_role`. La configurazione effettiva Vercel e i privilegi live non sono stati letti.
- **Verifiche codice:** 23 test Python mirati, 3 test UI Sito, 9 test gateway/impostazioni Agenda e `git diff --check` in entrambi i repository superati. Le prove controllano blocco e fail-closed ma non sostituiscono lo smoke test autenticato contro staging.
- **Problemi concreti:** nessuno rilevato nel collegamento e nelle transizioni simulate. **DA FARE:** prima di applicare la migrazione verificare che `DATABASE_URL` dell'ambiente di deploy usi il ruolo DB previsto e controllare lettura/attivazione/storico in staging. DB live invariato; nessun deploy.

## Diagnosi disponibilità e attivazione manutenzione, 14 ottobre 2026
- **VERIFICATO IN PRODUZIONE:** prima dell'attivazione, l'endpoint pubblico di disponibilità restituiva HTTP 503 perché `private.online_slot_status` non esisteva nello schema live verificato in sola lettura. La risposta chiedeva di riprovare; il flusso pubblico non poteva verificare date disponibili.
- **VERIFICATO IN PRODUZIONE:** lo stato manutenzione iniziale era `false`; dopo l'attivazione autorizzata dal pannello Agenda è `true`, con evento di attivazione presente nello storico amministrativo. La pagina pubblica ora mostra «La ciurma Makai è ai lavori!» e spiega che le prenotazioni online sono temporaneamente sospese.
- **Impatto corrente:** le prenotazioni online restano sospese intenzionalmente mentre la manutenzione è attiva. La funzione planner mancante è il problema tecnico originario e va ripristinata/verificata prima di disattivare la manutenzione.
- **Database:** nessuna migrazione o modifica di schema è stata applicata. L'unica mutazione live eseguita è l'attivazione tramite il pannello, con la corrispondente registrazione nello storico; le prenotazioni esistenti non sono state modificate.
- **DEPLOYATO:** le API Sito e la pagina manutenzione erano già presenti sul dominio pubblico durante la verifica; la pagina è stata controllata nel browser dopo l'attivazione. **DA FARE:** revisionare e autorizzare la migrazione che ripristina `private.online_slot_status`, poi provare l'endpoint di disponibilità prima di riaprire il servizio.

## Analisi motore coordinato v2 — 14 ottobre 2026
- **DA FARE:** adeguare API/UI Sito per le richieste DOPOCENA in attesa, idempotenza e risposta successiva di accettazione/rifiuto; il flusso attuale inserisce direttamente booking `confirmed` e dipende da `private.online_slot_status`, assente nell’ultimo inventario live di sola lettura.
- **IMPLEMENTATO LOCALMENTE:** nessuna modifica al codice Sito. Rapporto di verifica nel workspace Codex.
- **Verifiche/limiti:** nessun test v2; nessuna chiamata live di prenotazione. Il database live non è stato modificato.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** solo schema/metadati in sola lettura.


## Migrazione DB booking engine v2 — 14 ottobre 2026
- **DEPLOYATO:** migrazione `20261014002635` applicata a Supabase Production; conteggio confermato a 213 prenotazioni, RLS attiva, manutenzione attiva. Capienza fisica CENA 26; DOPOCENA in `manual_review`, senza assegnazione automatica. Nessuna prenotazione esistente aggiornata.
- **DA FARE prima della riapertura:** aggiornare API online affinché invii le richieste DOPOCENA alla nuova coda con idempotenza; l’API attuale non usa la coda e non è compatibile con il nuovo stato. Eseguire test end-to-end dopo la modifica.
- Nessun codice Sito modificato, nessun deploy applicativo. Rollback autonomo preparato e provato in PostgreSQL isolato, non applicato.


## Integrazione DOPOCENA v2 — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** l'API del Sito invia DOPOCENA alla coda privata v2 con retry idempotente; non crea subito `public.bookings`, non raccoglie il consenso marketing e non invia email/push. Il flusso CENA resta immediato con assegnazione SQL esistente. La pagina espone lo stato di richiesta non confermata.
- **Verifiche locali:** suite Python 146/146, JavaScript 9/9, build Vite superata; prova end-to-end dell'API contro PostgreSQL temporaneo: richiesta `pending`, replay idempotente, nessuna prenotazione; `git diff --check` superato.
- **DA FARE:** pubblicare insieme a Agenda; provare il flusso su Production con manutenzione ancora attiva. Messaggi di esito via email/WhatsApp non implementati in questo intervento.
- **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** database v2 verificato nel registro precedente; API/UI Sito non verificate live. Nessun commit, push o deploy.

## Push integrazione DOPOCENA v2 — 14 ottobre 2026
- **DEPLOYATO:** commit `4922faddbd68e086ad1b3d93c89e156243020aa8` inviato a `origin/main`; stato Vercel del commit `success` con descrizione «Deployment has completed».
- **VERIFICATO IN PRODUZIONE:** `GET https://www.makaipigneto.it/api/site-maintenance` ha risposto HTTP 200 con `{"active":true}` dopo il push. Non è stata inviata alcuna prenotazione live; il nuovo percorso DOPOCENA non è ancora verificato sul dominio.
- **DA FARE:** controllo coordinato con Agenda e prova controllata CENA/DOPOCENA prima di disattivare stabilmente la manutenzione. `.engram ` preesistente esclusa dal commit.

## Selezione servizio e orario a pulsanti — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** sostituiti i menu a tendina della pagina prenotazioni con due schede CENA/DOPOCENA e una griglia di orari. Selezione oro, spunta sul servizio, controlli radio nativi utilizzabili da tastiera, focus visibile e layout a tre colonne per gli orari su mobile. Gli slot continuano a provenire dalle impostazioni API; cambio servizio azzera orario e data, cambio orario azzera la data e richiede disponibilità aggiornata. Nei contatti compare il riepilogo al posto del secondo menu.
- **Evidenze:** codice e diff ispezionati; build Vite riuscita (53 moduli), controllo whitespace superato. Nessun test automatico o controllo visuale browser/dispositivo eseguito in questo intervento.
- **DA FARE:** controllo visuale e interazione su desktop/telefono, pubblicazione su richiesta. Nessuna modifica ad API, database o regole prenotazioni.
- **DEPLOYATO:** no per questa modifica. **VERIFICATO IN PRODUZIONE:** no. Nessun commit o push.

## Consenso marketing DOPOCENA e verifica chiusura CENA — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** il modulo mostra anche per DOPOCENA lo stesso consenso marketing facoltativo di CENA. La checkbox resta deselezionata; l'accettazione privacy rimane obbligatoria e separata.
- L'API riusa il salvataggio CENA per testo/versione del consenso, prova della checkbox, timestamp e scadenza di 24 mesi. Per DOPOCENA il consenso viene registrato solo quando la nuova richiesta `pending` è inserita; non crea una prenotazione e i replay idempotenti non rinnovano il consenso.
- **Verifica read-only dello schema live:** `marketing_contacts.booking_id` è nullable e timestamp/scadenza sono obbligatori; non serve una modifica SQL per registrare un consenso collegato a una richiesta non ancora accettata.
- **Verifica read-only live:** `online_booking_closures` produce `closed` soltanto per `service='normale'`; DOPOCENA passa a `manual_review`. La chiusura del lunedì resta comune a entrambi e `private.site_maintenance.active` risulta `false` al controllo. Nessun dato è stato scritto nel database; non è stata inviata una prenotazione di prova.
- **Verifiche locali:** test booking/API/disponibilità 27/27; suite Python completa 146/146; JavaScript 10/10; build Vite superata (53 moduli); `git diff --check` superato.
- Il DOPOCENA resta in revisione manuale; questo cambiamento non introduce conferme o disdette automatiche, né email o WhatsApp automatici. Nessuna modifica al motore dei tavoli.
- **DEPLOYATO:** no per il codice modificato. **VERIFICATO IN PRODUZIONE:** solo definizione SQL e nullable dello schema lette in sola lettura; UI/API aggiornate non verificate live. Nessun commit, push o deploy.

## Hero homepage — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** `HeroSection.jsx` usa le otto immagini presenti in `public/images`: `carne-osso.webp`, `MENU56.webp`, `panino.webp`, `menu.webp`, `sushi.webp`, `Udon di oden .webp`, `sushi2.webp` e `drinktop.webp`. Su mobile e sui dispositivi rilevati come meno potenti monta soltanto le prime quattro, in collage statico 2×2; su desktop monta la sequenza completa e il doppio necessario per il loop orizzontale lento. Il testo i18n resta fermo su un pannello scuro; la navigazione esistente non è stata cambiata. `prefers-reduced-motion` disattiva l’animazione CSS.
- **Evidenze locali (14 ottobre):** test JavaScript 12/12; build Vite riuscita (53 moduli); `git diff --check` superato. Percorsi degli otto file verificati sul disco.
- **Limiti:** nessuna verifica visuale su browser, telefono o produzione; il rilevamento hardware leggero usa API opzionali del browser con fallback. Le prime quattro immagini nell’elenco sono la scelta mobile. Le due cancellazioni preesistenti `public/images/panino.jpg`, `public/images/sushi2.jpg` e `.engram ` non sono state toccate.
- **DA FARE:** controllo visuale responsive e, se necessario, scelta definitiva delle quattro foto mobile. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.

## Anteprima homepage locale durante manutenzione — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** in modalità sviluppo la homepage `/` resta visibile senza pannello anche se l'API locale segnala manutenzione o non risponde. Le pagine prenotazioni continuano a rispettare il blocco; la deroga non è attiva nelle build/ambienti production.
- **Verifiche precedenti della modalità esplicita:** suite JavaScript 12/12 e build Vite 53 moduli; la modifica da anteprima con query a comportamento automatico locale non è stata verificata con test/build in questo passaggio.
- **DA FARE:** verificare la homepage in locale. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessuna modifica allo stato di manutenzione remoto o al database.

## Hero homepage secondo riferimento visivo — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** collage 2×2 mobile con le immagini approvate, testo centrato oro/avorio sopra sfumatura scura, marchio, separatore decorativo e CTA localizzata “Info”/“About” verso `#chi-siamo`. Desktop conserva lo scorrimento lento delle otto immagini; reduced-motion resta rispettato. Nessun intervento alla navigazione globale o al backend.
- **Verifiche locali:** test JavaScript 12/12, build Vite riuscita (53 moduli), `git diff --check` superato.
- **DA FARE:** controllo visuale nel browser locale alle dimensioni del riferimento e rifinitura di ritagli/spazi se necessari. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.

## Hero: titolo, teschio e sfondo condiviso — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** rimosso il pulsante Info/About e i relativi testi/stili. Titolo in Cormorant Garamond Semibold, WOFF2 latino locale da 23.4 KB con licenza OFL inclusa; il font rasterizzato nel riferimento non è identificabile con certezza, quindi questo è un adattamento visivo. Il separatore usa la sagoma dorata del teschio ricavata dal riferimento dell'utente, in SVG trasparente da 1.7 KB. Rimossi fondo nero della hero e sfumature del pannello: lo sfondo Tramonto condiviso torna visibile dietro l'intestazione e negli spazi del collage.
- **Evidenze correnti:** JavaScript 12/12, build Vite 53 moduli e controllo whitespace superati. Chromium locale osservato a 390×844 e 1440×900: font e teschio caricati, CTA assente, quattro foto statiche su mobile, larghezza documento uguale al viewport. Desktop con movimento lento; emulazione reduced-motion con animazione disattivata. Anteprime salvate nel workspace Codex.
- **Limiti:** browser con API simulate e hardware standard simulato; nessuna richiesta a database/API reali, verifica su iPhone fisico o produzione. **DA FARE:** valutazione finale visiva dell'utente e controllo su dispositivo reale. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.

## Contrasto leggero hero — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** solo CSS hero: velo nero al 16% sulle fotografie, alone ellittico compatto dietro al testo con bordi trasparenti e ombre delle lettere ridotte a 7–8 px. Sfondo condiviso, font, teschio e composizione conservati.
- **Evidenze correnti:** build Vite 53 moduli e `git diff --check` superati; controllo Chromium locale a 390×844 e 1440×900 e modalità reduced-motion. Foto statiche mobile, movimento desktop disattivato con reduced-motion, nessun debordo orizzontale. Screenshot mobile aggiornato e ispezionato; API simulate, nessuna connessione al database reale.
- **DA FARE:** valutazione visiva dell'utente e controllo su dispositivo fisico. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.

## Sfumatura centrale hero secondo riferimento — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** sostituito il lieve alone precedente con una sfumatura centrale più scura, da nero al 92% a trasparenza, estesa dietro il blocco testo; ellisse esplicita per dissolvere i bordi senza tagli rettangolari. Velo verticale sulle foto più intenso al centro e più leggero alle estremità. Ombre delle lettere alleggerite. Perimetro: CSS hero; foto, font e teschio conservati, pulsante Info ancora rimosso.
- **Evidenze correnti:** build Vite 53 moduli e controllo whitespace superati. Browser Chromium locale: 390×844, 390×693 (proporzioni del riferimento), 1440×900 e reduced-motion. Screenshot mobile confrontati/ispezionati; caricamento font/teschio, quattro foto mobile, assenza di CTA e debordo verificati. API simulate.
- **DA FARE:** valutazione visiva dell'utente; non è certificata un'identità pixel per pixel con il raster di riferimento, che usa immagini diverse. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push, deploy o intervento a database/API reali.

## Intestazione Chi siamo — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** solo intestazione della sezione homepage: titolo Pirata One oro chiaro con ombra scura, separatore dorato con teschio già usato nella hero e piccoli rombi. Selettori CSS specifici della homepage; nessuna modifica alla pagina di dettaglio o agli altri titoli.
- **Evidenze correnti:** build Vite 53 moduli e controllo whitespace superati. Chromium locale a 390×844 e 1440×900: teschio caricato e nessun debordo. Confronto prima/dopo del corpo della sezione superato: testo, collegamento, immagini/dimensioni e stili del pannello/foto uguali. Anteprima mobile ispezionata; API simulate.
- **DA FARE:** controllo dell'utente e su dispositivo reale. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.

## Intestazioni Menu, Eventi e Contatti — 14 ottobre 2026
- **IMPLEMENTATO LOCALMENTE:** esteso ai soli tre titoli principali della homepage il trattamento approvato per Chi siamo: Pirata One oro chiaro, ombra scura e separatore con teschio/rombi. Componente `HomeSectionHeading` condiviso e stesse regole CSS del titolo Chi siamo; testo localizzato e ID accessibili conservati. Il corpo delle tre sezioni e le pagine di dettaglio non sono stati modificati.
- **Evidenze correnti:** build Vite 54 moduli e controllo whitespace superati. Chromium locale, API simulate, 390×844 e 1440×1000, italiano/inglese: 12 confronti del corpo prima/dopo superati (HTML, testi, link, foto, controlli e stili/dimensioni invariati). Teschio caricato, titoli oro e nessun debordo. Tre anteprime mobile ispezionate.
- **DA FARE:** valutazione finale dell'utente e controllo su dispositivo fisico. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy. La modifica preesistente ad `AGENTS.md` è stata letta e preservata.

## Gestione cliente e ripristino schema prenotazioni — 15 ottobre 2026
- **Perimetro:** audit del backend nel repository Sito, aggiornamento locale di API, pagina `/prenotazioni/gestisci`, informativa privacy e test. Le modifiche preesistenti al Sito sono state preservate.
- **IMPLEMENTATO LOCALMENTE:** la richiesta cliente usa un identificativo per l'idempotenza; modifica CENA disponibile e cancellazione hanno esito immediato, indisponibilità e DOPOCENA restano richieste pendenti. L'API genera il link nello stesso commit della prenotazione, evita di ruotarlo al replay e tenta l'email di modifica/cancellazione solo dopo il commit. Pagina unica aggiornata per gli esiti reali; nessun account cliente.
- **Verifiche locali:** suite Python 146/146, JavaScript 12/12 e build Vite riuscite; migrazione SQL provata due volte su copia dello schema Production in PostgreSQL isolato, con test dei flussi cliente e rollback. Prova API integrata sulla stessa istanza locale: prenotazione CENA, ricevuta e token nello stesso commit, replay senza rotazione del link, modifica/cancellazione e rollback se il token non può essere creato. Nessuna prova browser/dispositivo.
- **DEPLOYATO:** il codice Sito di questo intervento non è stato pubblicato. Lo schema Supabase `20261015012424` è applicato; il Sito Production resta in manutenzione.
- **VERIFICATO IN PRODUZIONE:** dopo la migrazione, 213 prenotazioni e 86 ricevute online risultano conservate, RLS attiva, tabella token e funzioni cliente presenti, manutenzione attiva. Nessuna prenotazione CENA di prova o email reale inviata.
- **DA FARE:** pubblicazione coordinata del Sito e verifica controllata CENA, link, modifica, cancellazione e invio email prima della riapertura. Il codice backend eseguito in Production non è stato confrontato direttamente con l'artefatto Vercel.

## Preparazione rilascio gestione cliente — 15 ottobre 2026
- **Perimetro:** verifica finale nel checkout Mac effettivo, confronto con `origin/main` (`53b395e9`), migrazione Supabase già applicata e selezione dei soli file prenotazioni/API/privacy/test. Le modifiche grafiche della homepage e gli altri file preesistenti restano esclusi dal pacchetto di rilascio. Il backend distribuito è `api/` in questo repository, non la copia separata `backend-makai`.
- **IMPLEMENTATO LOCALMENTE:** pacchetto Sito/backend preparato nell'indice Git senza commit. Sul checkout e su una copia esatta di `HEAD` con i soli file candidati: Python 146/146, JavaScript 12/12, build Vite riuscite; diff staged senza errori whitespace.
- **VERIFICATO IN PRODUZIONE:** migrazione `20261015012424` nel registro, 213 prenotazioni, 86 ricevute, 0 token/operazioni cliente, RLS attiva, manutenzione `active=true`; `GET /api/health` e pagina gestione rispondono HTTP 200. Il flusso cliente aggiornato non è stato collaudato live.
- **DEPLOYATO:** nessun nuovo codice Sito/backend. Il tentativo di commit è stato respinto dalla revisione automatica: l'ordine di pubblicazione non è stato ritenuto autorizzazione esplicita separata a commit/push/deploy. Nessun push/deploy eseguito.
- **DA FARE:** autorizzazione separata esplicita per commit, push e deploy; poi collaudo coordinato con Agenda/email, senza riapplicare SQL e mantenendo la manutenzione attiva fino ai controlli fondamentali.


## Moduli e conferme: tono Makai e coerenza esiti — 17 ottobre 2026
- **Perimetro:** solo pagina prenotazioni e gestione cliente; chatbot escluso su indicazione esplicita dell’utente. Inventariati i form frontend; le risposte server sono state lette per confrontare il contratto degli esiti, senza modificare Backend, database, consensi o configurazioni. Modifiche preesistenti preservate.
- **IMPLEMENTATO LOCALMENTE:** messaggi di caricamento, disponibilità, validazione browser, errori, conferma, richiesta pendente, accettazione/rifiuto, cancellazione, modifica e riconferma con richiami pirateschi leggeri. Helper `src/i18n/bookingFeedback.js` condiviso dai due moduli. Testo consenso privacy/marketing invariato; vincoli nativi preservati e spiegazioni cancellate alla correzione dell’input.
- **Coerenza:** richiesta DOPOCENA pending esplicitamente non confermata; accettazione senza promessa di tavolo o contatto futuro automatico; cancellazione riferita al tavolo solo se assegnato; esiti sconosciuti non trasformati in conferme o richieste pendenti; risposta incerta non presentata come mancato salvataggio. Conferma CENA con data, persone e orario. Gestione cliente conserva la lingua italiana preesistente; feedback prenotazione allineati IT/EN. Dettagli applicativi restituiti dal server conservati dopo un’introduzione a tema, senza inventare traduzioni dei vincoli.
- **Evidenze locali:** suite JavaScript 17/17 (12 esistenti e 5 mirati ai messaggi/esiti), build Vite riuscita con 56 moduli, `git diff --check` superato. Ispezionati i diff dei due moduli e il contratto API; nessuna prenotazione inviata e nessuna comunicazione generata.
- **DA FARE:** controllo visuale e interattivo su browser/iPhone, in particolare gli avvisi nativi di validazione; successiva prova controllata dei flussi su ambiente autorizzato. I test dei messaggi non certificano il flusso API/database end-to-end. Chatbot rimandato a un intervento successivo.
- **DEPLOYATO:** no per questo intervento. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.


## Controllo collegamento conferma ed email — 17 ottobre 2026
- **Perimetro:** ispezione in sola lettura di `backend-makai/app.py`, `api/booking_communications.py` e test esistenti `tests/test_online_api.py`, dopo la revisione testi Sito. Nessuna modifica applicativa.
- **IMPLEMENTATO LOCALMENTE (presenza verificata):** per una nuova prenotazione CENA salvata e confermata con email compilata, la route chiama automaticamente il mittente già esistente dopo il salvataggio e prima di restituire la risposta, a seguito del tentativo push. Invio tramite claim e funzione email configurata; replay senza reinvio automatico. DOPOCENA pending non invia conferma; email facoltativa vuota non attiva invio. Un errore email non annulla la prenotazione. I testi frontend modificati non cambiano questo percorso.
- **Evidenze e limiti:** codice e test ispezionati; nessun test eseguito in questo controllo, nessuna email inviata, nessuna verifica runtime o consegna al destinatario.
- **DA FARE:** prova controllata dell’intero percorso Sito → Agenda → email; distinguere tentativo, accettazione provider e consegna. **DEPLOYATO:** nessun nuovo rilascio. **VERIFICATO IN PRODUZIONE:** no in questo controllo. Nessun commit, push, deploy o modifica database.

## Audit messaggi dei comandi pubblici — 17 ottobre 2026
- **Perimetro:** revisione locale dei feedback azionati da form e pulsanti del Sito, compresa la pagina di gestione cliente; chatbot escluso come concordato. Conservate tutte le modifiche preesistenti al checkout.
- **IMPLEMENTATO LOCALMENTE:** testi della gestione cliente ora seguono la lingua attiva anche se cambia dopo la comparsa di un errore; status sconosciuti sono mostrati come “da verificare” invece di esporre valori tecnici. Aggiunta la traduzione del messaggio backend di servizio temporaneamente non disponibile. Le conferme distinguono presenza riconfermata, modifica applicata, richiesta pendente non ancora approvata e cancellazione; la richiesta pendente ribadisce che la prenotazione attuale resta invariata e confermata.
- **Coerenza dei comandi:** le etichette/istruzioni operative restano dirette e leggibili, con richiami pirateschi leggeri nei feedback, caricamenti e registro di bordo. I messaggi esistenti di disponibilità e validazione dei moduli di prenotazione restano nell’ambito Makai. Nessuna modifica a chatbot, logica di prenotazione, API, email, consensi o dati.
- **Evidenze e limiti:** confronto statico delle stringhe frontend con gli esiti/errore API già ispezionati; `git diff --check` superato. In questo intervento non eseguiti test, build, browser, invii di prenotazione/email o controlli live.
- **DA FARE:** verifica interattiva sul browser e controllo dei feedback in inglese durante il cambio lingua. **DEPLOYATO:** no. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.


## Audit testi e invii email — 17 ottobre 2026
- **Perimetro:** lettura del flusso Sito → Backend → Edge `send-booking-email` → Resend, dei template locali Agenda `supabase/functions/agenda-communications/messages.js`, delle RPC/trigger SQL versionati e delle istruzioni del reminder. Nessuna email inviata e nessuna modifica applicativa o database.
- **IMPLEMENTATO LOCALMENTE (presenza verificata):** il codice preesistente compone i template nel file Agenda indicato; Backend prepara/legge comunicazione, claim, invoca Edge e registra l’esito. La prenotazione CENA online confermata con email valida tenta l’invio dopo il commit; email assente, prenotazione DOPOCENA ancora pending e replay non attivano quel tentativo automatico. Modifiche applicate e cancellazioni richieste dal cliente tentano l’invio dopo il commit; richieste cliente pendenti non generano email automatica. Gli inserimenti/modifiche staff e i template reminder, riconferma, ritardo e alternativa passano dalla coda e invio esplicito Agenda. Nessuno scheduler reminder risulta configurato nel codice esaminato.
- **Testi da definire prima di un’eventuale modifica:** il template `reminder` include anche la frase “La mancata riconferma non annulla la prenotazione”, benché il corpo reminder non chieda una riconferma; il template `delay` chiede di comunicare l’orario di arrivo senza indicare chiaramente il canale. Il rifiuto DOPOCENA è presente nel generatore testi, ma non è tra i tipi email ammessi dall’Edge/Backend esaminati; il flusso Agenda lo propone via WhatsApp precompilato, non come email automatica. I messaggi restano sobri con richiami Makai/pirateschi leggeri; “accepted” indica accettazione Resend, non consegna.
- **Evidenze e limiti:** ispezionati sorgenti e documentazione locali nei checkout Sito, Backend e Agenda, inclusi i working tree già modificati dall’utente; nessuna modifica a quei cambiamenti. Versioni locali e codice deployato possono divergere: non controllata la versione Edge in produzione, la configurazione runtime, l’Agenda autenticata, l’esito Resend o la consegna. Nessun test, build o invio eseguito.
- **DA FARE:** definire il testo e il canale del reminder, il modo di rispondere a un ritardo, e se il rifiuto DOPOCENA debba restare WhatsApp manuale o avere un flusso email separato. **DEPLOYATO:** nessuna modifica in questo intervento. **VERIFICATO IN PRODUZIONE:** no. Nessun commit, push o deploy.


## Verifica pagina gestione da link email — 17 ottobre 2026
- **Perimetro:** verifica della route `/prenotazioni/gestisci`, dei rewrite Vercel, del gateway Sito, della gestione del token e del template Edge attivo. Nessun token cliente usato, prenotazione modificata o email inviata.
- **IMPLEMENTATO LOCALMENTE:** la route esiste in `src/app.jsx`; il build include il chunk `BookingManagementPage`. Il link è generato con token nel fragment `#token=...`; la pagina legge quel fragment, poi chiama `/api/booking-management/view|request|reconfirm`. Il gateway ammette le tre operazioni POST e il rewrite Vercel inoltra le altre route all’app SPA.
- **VERIFICATO IN PRODUZIONE:** navigazione browser a `/prenotazioni/gestisci` raggiunge la pagina Makai e rende il titolo “La tua prenotazione”. Senza token, il Backend risponde “Richiesta non disponibile.”, esito atteso per questo controllo. I metadati Vercel associano il dominio pubblico al deployment Git `e233f74c02e2f5da37433345076038975df09e06`, nel cui sorgente la route è presente.
- **Email:** lettura Supabase in sola lettura della Edge Function `send-booking-email`, attiva versione 21; il template include il collegamento di gestione quando lo snapshot contiene un URL HTTPS conforme. Il codice locale online genera il token e lo aggiunge allo snapshot queued. Nessuna prova di un messaggio realmente ricevuto e nessun test con token valido: generazione live dello snapshot e accesso/modifica/cancellazione di una prenotazione non sono certificati.
- **Evidenze e limiti:** build Vite locale riuscita (56 moduli). La navigazione pubblica senza token non può dimostrare il flusso cliente completo. Nessuna modifica applicativa, database, invio, commit, push o deploy; working tree preesistenti preservati. **DA FARE:** se il cliente non riesce a usare il link, controllare in modo controllato il contenuto della sua email e verificare con un token di test isolato il caricamento, la modifica e la cancellazione. **DEPLOYATO:** nessuna modifica in questo intervento.
