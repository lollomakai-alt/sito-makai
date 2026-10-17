# Istruzioni progetto — Sito Makai

## Letture obbligatorie prima di ogni intervento
- Leggi questo file e poi [stato e attività del Sito](MAKAI_SITO_STATO_E_TODO.md) e [roadmap comune dell'ecosistema](../MAKAI_ECOSISTEMA_STATO_E_ROADMAP.md).
- Controlla `git status` e preserva ogni modifica preesistente.
- Per interventi sul backend condiviso, leggi anche [stato del Backend](../MAKAI_BACKEND_STATO_E_TODO.md). Dal 16 ottobre 2026 il backend condiviso è pubblicato nel progetto Vercel `backend-makai`; questo repository contiene il gateway Node pubblico `api/backend-gateway.mjs`. I 50 vecchi file Python/API, test e script del Sito sono conservati nell'archivio `../backups/backend-cutover-2026-10-16/sito-backend-originale.tar.gz` con manifesto SHA-256. Segui anche le istruzioni del progetto Backend per gli interventi condivisi.

## Confini
- Segui le protezioni generali: nessuna modifica a codice, database o configurazione produzione durante attività documentali; niente commit, push o deploy senza richiesta esplicita.
- Le regole prenotazioni sono condivise con Agenda e database: non dedurre che uno stato locale sia live.
- Alla fine aggiorna [stato e attività del Sito](MAKAI_SITO_STATO_E_TODO.md) con evidenze e limiti, usando le quattro categorie di stato definite nelle istruzioni generali.
