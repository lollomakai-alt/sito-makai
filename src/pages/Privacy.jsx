import SiteNav from "../components/SiteNav";
import { useLanguage } from "../i18n/LanguageContext";

const ragioneSociale = import.meta.env.VITE_RAGIONE_SOCIALE;
const piva = import.meta.env.VITE_PIVA;
const indirizzo = import.meta.env.VITE_INDIRIZZO;
const emailPrivacy = import.meta.env.VITE_EMAIL_PRIVACY;

const privacyCopy = {
  it: {
    title: "Informativa sulla privacy",
    updated: "Ultimo aggiornamento: 4 ottobre 2026",
    headings: ["1. Titolare del trattamento", "2. Quali dati raccogliamo", "3. Perché li usiamo e su quale base", "4. Per quanto tempo li conserviamo", "5. Chi può accedere ai dati", "6. I tuoi diritti", "7. Cookie"],
    controller: "Il titolare gestisce il locale Makai Grand Line.",
    data: "Quando prenoti tramite il modulo sul sito o telefonicamente raccogliamo: nome, numero di telefono, eventuale email, data e ora, numero di persone ed eventuali note che fornisci (per esempio richieste particolari). Ti chiediamo di non inserire nelle note informazioni sulla tua salute. Se accetti di ricevere offerte e novità, conserviamo anche la prova del consenso, il canale e la data in cui è stato espresso, il numero delle visite registrate e la data dell'ultima visita.",
    purposes: [
      ["Gestire la tua prenotazione", ", contattarti in caso di necessità. Il modulo online conferma sul sito e non invia email automatiche. Base giuridica: esecuzione della tua richiesta (art. 6.1.b GDPR)."],
      ["Ricordare i tuoi dati per prenotazioni future", ", solo se spunti la casella apposita. Base giuridica: il tuo consenso (art. 6.1.a GDPR). Puoi revocarlo in qualsiasi momento senza conseguenze sulla prenotazione."],
      ["Inviarti offerte e novità via email o WhatsApp", ", compreso un eventuale messaggio in occasione del tuo compleanno, e ricordare il numero delle tue visite per iniziative dedicate, solo dopo un consenso separato ed esplicito. Base giuridica: il tuo consenso (art. 6.1.a GDPR). Puoi revocarlo in qualsiasi momento, senza conseguenze sulla prenotazione."],
    ],
    required: "Il conferimento dei dati per la prenotazione è necessario: senza non possiamo confermarla. La lettura dell’informativa privacy e il consenso marketing sono separati. La casella offerte WhatsApp del modulo online è facoltativa e non preselezionata.",
    retention: [
      "Dati della prenotazione: 30 giorni dopo la data della prenotazione, poi cancellati automaticamente.",
      "Se hai dato il consenso a essere ricordato: 12 mesi dalla data della prenotazione, poi cancellati automaticamente.",
      "Offerte, novità e conteggio delle visite: 24 mesi dalla data del consenso. Se presti nuovamente il consenso in occasione di una nuova prenotazione, il periodo riparte dalla nuova data. In caso di revoca, l'invio e il conteggio cessano immediatamente.",
      "I messaggi della chat non vengono conservati oltre la conversazione. [VERIFICA]",
    ],
    accessIntro: "I dati sono trattati dal personale autorizzato del locale e dai fornitori tecnici che ci aiutano a far funzionare il servizio, nominati responsabili del trattamento:",
    providers: ["Supabase (database), con server nell'Unione Europea (Francoforte).", "[NOME HOSTING DEL BACKEND] (hosting del sito e del servizio di prenotazione).", "[NOME SERVIZIO EMAIL] (invio dei promemoria e delle offerte)."],
    automation: "La chat di prenotazione funziona con regole automatiche interne e non invia i tuoi messaggi a servizi di intelligenza artificiale esterni. [VERIFICA] Non vendiamo i tuoi dati e non li usiamo per profilazione.",
    transfers: "[SE UN FORNITORE TRATTA DATI FUORI DALLA UE, INDICALO QUI CON LE GARANZIE USATE, ES. CLAUSOLE CONTRATTUALI STANDARD.]",
    rights: "Puoi chiedere in qualsiasi momento accesso ai tuoi dati, rettifica, cancellazione, limitazione del trattamento, opposizione e portabilità, e revocare il consenso dato.",
    authority: "Se ritieni che il trattamento violi la legge, puoi presentare reclamo al Garante per la protezione dei dati personali (www.garanteprivacy.it).",
    response: "rispondiamo entro un mese.",
    cookies: "Il sito usa solo strumenti tecnici necessari al funzionamento (per esempio l'accesso riservato al personale). Non usiamo cookie di profilazione o di analisi. [VERIFICA: se aggiungi analytics o pixel, va aggiornato e serve un banner.]",
    back: "← Torna al sito",
  },
  en: {
    title: "Privacy Policy",
    updated: "Last updated: 4 October 2026",
    headings: ["1. Data controller", "2. Data we collect", "3. Why we use your data and our legal basis", "4. How long we retain your data", "5. Who can access your data", "6. Your rights", "7. Cookies"],
    controller: "The data controller operates the Makai Grand Line venue.",
    data: "When you book through the website form or by phone, we collect your name, phone number, optional email address, booking date and time, number of guests and any notes you provide, such as special requests. Please do not include health information in the notes. If you agree to receive offers and news, we also retain evidence of your consent, the channel and the date on which it was given, the number of recorded visits and the date of your last visit.",
    purposes: [
      ["Managing your booking", ", contacting you when necessary. The online form confirms on the website and does not send automatic emails. Legal basis: performance of your request (Article 6(1)(b) GDPR)."],
      ["Remembering your details for future bookings", ", only when you select the relevant option. Legal basis: your consent (Article 6(1)(a) GDPR). You may withdraw it at any time without affecting your booking."],
      ["Sending offers and news by email or WhatsApp", ", including an optional birthday message, and remembering your number of visits for dedicated initiatives, only after separate and explicit consent. Legal basis: your consent (Article 6(1)(a) GDPR). You may withdraw consent at any time without affecting your booking."],
    ],
    required: "Providing the data required for a booking is necessary; without it, we cannot confirm your booking. Reading the privacy policy and marketing consent are separate. The website form’s WhatsApp offers checkbox is optional and unchecked by default.",
    retention: ["Booking data: 30 days after the booking date, then automatically deleted.", "If you consented to being remembered: 12 months from the booking date, then automatically deleted.", "Offers, news and visit count: 24 months from the date of consent. If you consent again when making a new booking, the period restarts from the new date. Messaging and visit counting stop immediately if you withdraw consent.", "Chat messages are not retained beyond the conversation. [VERIFY]"],
    accessIntro: "Your data is processed by authorised venue staff and by the technical providers that help us operate the service, appointed as data processors:",
    providers: ["Supabase (database), with servers in the European Union (Frankfurt).", "[BACKEND HOSTING PROVIDER NAME] (website and booking service hosting).", "[EMAIL SERVICE NAME] (booking reminders and offers)."],
    automation: "The booking chat uses internal automated rules and does not send your messages to external artificial intelligence services. [VERIFY] We do not sell your data or use it for profiling.",
    transfers: "[IF A PROVIDER PROCESSES DATA OUTSIDE THE EU, STATE IT HERE AND DESCRIBE THE SAFEGUARDS USED, E.G. STANDARD CONTRACTUAL CLAUSES.]",
    rights: "You may request access to your data, rectification, deletion, restriction of processing, objection and portability at any time, and you may withdraw any consent you have given.",
    authority: "If you believe the processing infringes the law, you may lodge a complaint with the Italian Data Protection Authority (www.garanteprivacy.it).",
    response: "we will respond within one month.",
    cookies: "The website uses only technical tools required for its operation, such as restricted staff access. We do not use profiling or analytics cookies. [VERIFY: if analytics or pixels are added, this policy must be updated and a banner will be required.]",
    back: "← Back to the website",
  },
};

export default function Privacy() {
  const { language } = useLanguage();
  const copy = privacyCopy[language];

  return (
    <div className="scroll-container privacy-page">
      <SiteNav />
      <main className="privacy-main">
        <div className="privacy-card">
          <h1>{copy.title}</h1>
          <p className="privacy-updated">{copy.updated}</p>
          <h2>{copy.headings[0]}</h2>
          <p>{ragioneSociale}, {language === "en" ? "VAT number" : "P.IVA"} {piva}, {language === "en" ? "registered office at" : "sede in"} {indirizzo}, email {emailPrivacy}. {copy.controller}</p>
          <h2>{copy.headings[1]}</h2>
          <p>{copy.data}</p>
          <h2>{copy.headings[2]}</h2>
          <ul>{copy.purposes.map(([lead, text]) => <li key={lead}><strong>{lead}</strong>{text}</li>)}</ul>
          <p>{copy.required}</p>
          <h2>{copy.headings[3]}</h2>
          <ul>{copy.retention.map((item) => <li key={item}>{item}</li>)}</ul>
          <h2>{copy.headings[4]}</h2>
          <p>{copy.accessIntro}</p>
          <ul>{copy.providers.map((item) => <li key={item}>{item}</li>)}</ul>
          <p>{copy.automation}</p>
          <p>{copy.transfers}</p>
          <h2>{copy.headings[5]}</h2>
          <p>{copy.rights} {language === "en" ? "Write to" : "Scrivi a"} {emailPrivacy}; {copy.response}</p>
          <p>{copy.authority}</p>
          <h2>{copy.headings[6]}</h2>
          <p>{copy.cookies}</p>
          <a className="privacy-back" href="/">{copy.back}</a>
        </div>
      </main>
    </div>
  );
}
