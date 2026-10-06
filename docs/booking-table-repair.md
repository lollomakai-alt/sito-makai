# Recupero dei tavoli delle prenotazioni esistenti

La procedura non parte automaticamente e non ha un endpoint pubblico.

## DRY RUN (sola lettura)

Dalla cartella sito-makai:

```sh
.venv/bin/python scripts/repair_booking_tables.py --report /private/tmp/makai-tavoli-report.json
```

Usare un nuovo percorso per ogni report. Il file contiene nomi: conservarlo fuori dal repository e non pubblicarlo.
La transazione è READ ONLY. Il report include tutte le prenotazioni confirmed future con party_size >= 1 e tables NULL, vuoto o composto da spazi.
L'ordine è booking_date, booking_time, id. La simulazione usa _find_tables(), TABLES e JOINABLE_ROWS e tiene conto sia dei tavoli già assegnati (anche a prenotazioni successive sovrapposte), sia delle assegnazioni proposte ai record precedenti.
Le assegnazioni bloccano la giornata prenotata senza riuso a tempo, come le nuove prenotazioni. Arrived e completed con tavolo assegnato restano bloccanti; cancelled/no_show sono esclusi. I report creati con la precedente politica devono essere rigenerati. Non vengono imposti ai record storici i limiti online di 6 persone o 60 giorni: si cercano solo combinazioni realmente consentite.
I gruppi senza sistemazione rimangono invariati, con TAVOLO DA ASSEGNARE nell'Agenda. I loro tavoli non sono deducibili: nessuna assegnazione viene inventata. Il calendario pubblico usa la stessa ricostruzione esclusivamente in memoria: un tavolo vuoto non blocca più la giornata se ricostruibile. I casi non ricostruibili restano non verificabili. Le nuove prenotazioni ricostruiscono l'occupazione sotto il lock di scrittura e salvano solo la propria assegnazione valida.

## Applicazione: solo dopo conferma esplicita del report

```sh
.venv/bin/python scripts/repair_booking_tables.py --report /private/tmp/makai-tavoli-report.json --apply-approved-report
```

Il comando acquisisce il lock condiviso con le altre operazioni di prenotazione e un lock della tabella contro scritture concorrenti anche da altre applicazioni.
Rilegge l'agenda e ricalcola tutto. Qualsiasi differenza nei dati, nella configurazione o nelle proposte interrompe l'operazione; serve un nuovo report da approvare.
Aggiorna esclusivamente tables dei record confirmed ancora vuoti. Non cambia nominativi, date, orari, stato, consensi o prenotazioni già assegnate e non cancella nulla.
Le modifiche sono atomiche: un errore annulla l'intera transazione.
Rieseguire il DRY RUN dopo l'applicazione non ripropone i record assegnati. Riutilizzare il vecchio report viene rifiutato senza modifiche. I record irrisolti possono essere riproposti solo con un nuovo report e nuova conferma.
