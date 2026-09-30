import SiteNav from "../components/SiteNav";

const ragioneSociale = import.meta.env.VITE_RAGIONE_SOCIALE;
const piva = import.meta.env.VITE_PIVA;
const indirizzo = import.meta.env.VITE_INDIRIZZO;
const emailPrivacy = import.meta.env.VITE_EMAIL_PRIVACY;

// Informativa privacy - sostituisci tutto ciò che è tra [PARENTESI QUADRE].
// Da verificare prima di pubblicare: tempi (30 giorni / 12 mesi), messaggi chat non conservati, fornitori.
export default function Privacy() {
  return (
    <div className="scroll-container privacy-page">
      <SiteNav />

      <main className="privacy-main">
        <div className="privacy-card">
          <h1>Informativa sulla privacy</h1>
          <p className="privacy-updated">Ultimo aggiornamento: [DATA]</p>

          <h2>1. Titolare del trattamento</h2>
          <p>
            {ragioneSociale}, P.IVA {piva}, sede in {indirizzo}, email {emailPrivacy}.
            Il titolare gestisce il locale Makai Grand Line.
          </p>

          <h2>2. Quali dati raccogliamo</h2>
          <p>
            Quando prenoti tramite la chat raccogliamo: nome, numero di telefono, email, data e ora,
            numero di persone ed eventuali note che scrivi tu (per esempio richieste particolari).
            Ti chiediamo di non inserire nelle note informazioni sulla tua salute.
            Se spunti la casella per ricevere offerte e novità, conserviamo anche il tuo indirizzo email,
            il nome e la data del tuo consenso.
          </p>

          <h2>3. Perché li usiamo e su quale base</h2>
          <ul>
            <li>
              <strong>Gestire la tua prenotazione</strong>, contattarti in caso di necessità e inviarti
              il promemoria via email prima della serata. Base giuridica: esecuzione della tua richiesta
              (art. 6.1.b GDPR).
            </li>
            <li>
              <strong>Ricordare i tuoi dati per prenotazioni future</strong>, solo se spunti la casella
              apposita. Base giuridica: il tuo consenso (art. 6.1.a GDPR). Puoi revocarlo in qualsiasi
              momento senza conseguenze sulla prenotazione.
            </li>
            <li>
              <strong>Inviarti offerte e novità via email</strong>, solo se spunti la casella apposita.
              Base giuridica: il tuo consenso (art. 6.1.a GDPR). Ogni email contiene il link per annullare
              l'iscrizione e puoi revocare il consenso in qualsiasi momento, senza conseguenze sulla prenotazione.
            </li>
          </ul>
          <p>
            Il conferimento dei dati per la prenotazione è necessario: senza non possiamo confermarla.
            Il consenso a ricordare i dati e quello a ricevere offerte sono facoltativi e indipendenti l'uno dall'altro.
          </p>

          <h2>4. Per quanto tempo li conserviamo</h2>
          <ul>
            <li>Dati della prenotazione: 30 giorni dopo la data della prenotazione, poi cancellati automaticamente.</li>
            <li>Se hai dato il consenso a essere ricordato: 12 mesi dalla data della prenotazione, poi cancellati automaticamente.</li>
            <li>Offerte e novità via email: fino a quando annulli l'iscrizione.</li>
            <li>I messaggi della chat non vengono conservati oltre la conversazione. [VERIFICA]</li>
          </ul>

          <h2>5. Chi può accedere ai dati</h2>
          <p>
            I dati sono trattati dal personale autorizzato del locale e dai fornitori tecnici che
            ci aiutano a far funzionare il servizio, nominati responsabili del trattamento:
          </p>
          <ul>
            <li>Supabase (database), con server nell'Unione Europea (Francoforte).</li>
            <li>[NOME HOSTING DEL BACKEND] (hosting del sito e del servizio di prenotazione).</li>
            <li>[NOME SERVIZIO EMAIL] (invio dei promemoria e delle offerte).</li>
          </ul>
          <p>
            La chat di prenotazione funziona con regole automatiche interne e non invia i tuoi
            messaggi a servizi di intelligenza artificiale esterni. [VERIFICA]
            Non vendiamo i tuoi dati e non li usiamo per profilazione.
          </p>
          <p>[SE UN FORNITORE TRATTA DATI FUORI DALLA UE, INDICALO QUI CON LE GARANZIE USATE, ES. CLAUSOLE CONTRATTUALI STANDARD.]</p>

          <h2>6. I tuoi diritti</h2>
          <p>
            Puoi chiedere in qualsiasi momento accesso ai tuoi dati, rettifica, cancellazione,
            limitazione del trattamento, opposizione e portabilità, e revocare il consenso dato.
            Scrivi a {emailPrivacy}; rispondiamo entro un mese.
          </p>
          <p>
            Se ritieni che il trattamento violi la legge, puoi presentare reclamo al Garante per la
            protezione dei dati personali (www.garanteprivacy.it).
          </p>

          <h2>7. Cookie</h2>
          <p>
            Il sito usa solo strumenti tecnici necessari al funzionamento (per esempio l'accesso
            riservato al personale). Non usiamo cookie di profilazione o di analisi. [VERIFICA: se aggiungi analytics o pixel, va aggiornato e serve un banner.]
          </p>
          <a className="privacy-back" href="/">← Torna al sito</a>
        </div>
      </main>
    </div>
  );
}