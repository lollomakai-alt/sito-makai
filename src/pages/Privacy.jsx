import SiteNav from "../components/SiteNav";
import SiteHeading from "../components/SiteHeading";
import { useLanguage } from "../i18n/LanguageContext";

const ragioneSociale = "AMACA S.r.l.";
const piva = "13934581003";
const indirizzo = "Via dei Magazzini Generali 4, 00154 Roma";
const emailPrivacy = "makairoma@gmail.com";

const privacyCopy = {
  it: {
    title: "Informativa sulla privacy",
    updated: "Ultimo aggiornamento: 17 ottobre 2026",

    sections: {
      controller: "1. Titolare del trattamento",
      data: "2. Dati personali trattati",
      purposes: "3. Finalità e basi giuridiche",
      required: "4. Natura del conferimento",
      retention: "5. Conservazione dei dati",
      providers: "6. Destinatari e fornitori tecnici",
      transfers: "7. Trasferimenti internazionali",
      security: "8. Sicurezza",
      rights: "9. Diritti dell'interessato",
      authority: "10. Reclamo al Garante",
      cookies: "11. Cookie e strumenti tecnici",
      updates: "12. Modifiche all'informativa",
    },

    controller:
      "Il Titolare del trattamento gestisce il locale Makai Grand Line. Il Responsabile della protezione dei dati (DPO/RPD) nominato è Alessio Esposito, contattabile all'indirizzo email indicato sopra.",

    dataIntro:
      "Quando utilizzi il sito, effettui una prenotazione online, telefoni al locale o comunichi con il personale per una prenotazione, possiamo trattare i seguenti dati:",

    dataItems: [
      "nome indicato per la prenotazione;",
      "numero di telefono;",
      "indirizzo email, quando fornito o necessario per le comunicazioni relative alla prenotazione;",
      "data e ora della prenotazione;",
      "numero di persone;",
      "tavolo eventualmente assegnato;",
      "note e richieste inserite nella prenotazione;",
      "stato della prenotazione, comprese modifiche, cancellazioni e mancata presentazione;",
      "informazioni relative alle comunicazioni di servizio collegate alla prenotazione;",
      "richieste di modifica o cancellazione, decisioni dello staff e riconferme ricevute tramite il collegamento personale;",
      "testi inviati alla chat Nostromo e dati inseriti durante la conversazione; il contesto temporaneo della chat è trasmesso in un token firmato e scade dopo 30 minuti;",
      "dati delle richieste di inserimento in lista d'attesa, inclusi nome, telefono, email se fornita, data, orario, numero di persone, note, stato e storico delle modifiche;",
      "dati delle comunicazioni di servizio, come destinatario, canale, contenuto predisposto, stato di invio, identificativi del fornitore ed eventuali errori;",
      "indirizzo IP e dati tecnici usati temporaneamente per limitare gli abusi e proteggere il servizio;",
      "preferenza della lingua del sito, conservata nel browser tramite memoria locale;",
      "dati tecnici strettamente necessari al funzionamento e alla sicurezza del servizio.",
    ],

    sensitive:
      "Ti chiediamo di non inserire nelle note dati relativi alla salute o altre informazioni particolarmente sensibili, salvo quando strettamente necessario e dopo aver contattato direttamente il locale.",

    marketingData:
      "Se scegli volontariamente di ricevere comunicazioni promozionali, trattiamo inoltre i dati necessari a documentare il consenso, come data, canale, stato del consenso ed eventuale revoca.",

    purposes: [
      {
        title: "Gestione della prenotazione",
        text: "Utilizziamo i dati per registrare e gestire la prenotazione, verificare la disponibilità, assegnare il tavolo, gestire eventuali modifiche o cancellazioni e contattarti quando necessario. La chat Nostromo può essere usata per rispondere alle richieste e avviare una prenotazione; il relativo contesto è temporaneo. Base giuridica per la gestione della prenotazione: esecuzione di misure precontrattuali o del servizio richiesto, ai sensi dell'art. 6, par. 1, lett. b) GDPR.",
      },
      {
        title: "Comunicazioni di servizio",
        text: "Possiamo inviarti comunicazioni strettamente collegate alla prenotazione, come conferme, aggiornamenti, promemoria o comunicazioni operative. Le email di conferma possono essere inviate automaticamente. Il collegamento personale permette di riconfermare, modificare o cancellare la prenotazione. Le modifiche disponibili e le cancellazioni sono immediate; quando una modifica non è disponibile, la prenotazione resta invariata e lo staff riceve una richiesta. Il link scade 30 giorni dopo la prenotazione e non va condiviso. Queste comunicazioni non costituiscono marketing e sono funzionali alla gestione della prenotazione.",
      },
      {
        title: "Gestione operativa e storico delle prenotazioni",
        text: "Le informazioni relative a prenotazioni, richieste in lista d'attesa, modifiche, cancellazioni, arrivi, mancata presentazione e comunicazioni rilevanti possono essere utilizzate dal personale autorizzato per gestire il servizio e ricostruire gli eventi operativi collegati. Le comunicazioni possono essere registrate con il relativo stato tecnico di invio.",
      },
      {
        title: "Marketing e promozioni",
        text: "Comunicazioni promozionali tramite email, WhatsApp o altri canali vengono effettuate solo in presenza di uno specifico consenso facoltativo. Base giuridica: consenso, ai sensi dell'art. 6, par. 1, lett. a) GDPR. Il consenso può essere revocato in qualsiasi momento senza conseguenze sulla prenotazione.",
      },
    ],

    required:
      "Il conferimento dei dati necessari alla prenotazione è indispensabile per poterla gestire e confermare. Il consenso per finalità di marketing è invece facoltativo, separato dalla prenotazione e non è mai necessario per utilizzare i servizi del Makai.",

    retention: [
      "Le prenotazioni e i relativi dati operativi — incluse richieste DOPOCENA, richieste cliente, voci e storico della lista d'attesa, storico prenotazione, token, ricevute tecniche e log delle comunicazioni — sono cancellati automaticamente 30 giorni dopo la data del servizio o della richiesta.",
      "Il contesto temporaneo della chat Nostromo scade dopo 30 minuti. I messaggi non vengono salvati come cronologia chat nel database; se la conversazione porta a una prenotazione, i dati necessari vengono registrati nella prenotazione.",
      "I dati relativi al consenso marketing e alle attività promozionali sono conservati fino a 12 mesi dalla registrazione o dal rinnovo del consenso. La revoca interrompe subito l'uso promozionale; la prova del consenso resta conservata al massimo per 12 mesi dalla registrazione o dal rinnovo.",
      "Alcune informazioni possono essere conservate più a lungo quando ciò sia necessario per adempiere a obblighi di legge o tutelare un diritto, nel rispetto dei principi di necessità e minimizzazione.",
    ],

    providersIntro:
      "I dati possono essere trattati dal personale autorizzato del Makai e dai fornitori tecnici necessari al funzionamento del servizio. Tra i principali servizi utilizzati:",

    providers: [
      "Supabase, per database, autenticazione e servizi backend;",
      "Vercel, per hosting e distribuzione del sito e dei servizi backend;",
      "Resend, per l'invio delle email relative alle prenotazioni.",
      "WhatsApp/Meta, quando scegli di contattare il locale tramite WhatsApp o, se hai prestato il consenso, di ricevere comunicazioni promozionali tramite quel canale.",
    ],

    providersOutro:
      "I fornitori trattano i dati secondo i rispettivi ruoli, condizioni contrattuali e obblighi applicabili in materia di protezione dei dati. Makai non vende i dati personali degli utenti a terzi.",

    transfers:
      "Alcuni fornitori tecnologici possono utilizzare infrastrutture o subfornitori situati anche al di fuori dello Spazio Economico Europeo. Quando applicabile, i trasferimenti avvengono nel rispetto delle condizioni previste dal GDPR, tramite decisioni di adeguatezza o altre garanzie riconosciute dalla normativa, incluse le Clausole Contrattuali Standard.",

    security:
      "Adottiamo misure tecniche e organizzative volte a proteggere i dati personali da accessi non autorizzati, perdita, alterazione o divulgazione indebita. Le funzioni amministrative e gestionali sono riservate al personale autorizzato e i servizi backend utilizzano controlli di autenticazione e autorizzazione.",

    rightsIntro:
      "Nei casi previsti dal GDPR puoi esercitare i seguenti diritti:",

    rights: [
      "accesso ai dati personali;",
      "rettifica dei dati inesatti;",
      "cancellazione dei dati;",
      "limitazione del trattamento;",
      "portabilità dei dati, quando applicabile;",
      "opposizione al trattamento, quando applicabile;",
      "revoca del consenso in qualsiasi momento, senza pregiudicare la liceità del trattamento effettuato prima della revoca.",
    ],

    rightsContact:
      "Per esercitare i tuoi diritti puoi scrivere all'indirizzo email indicato nell'informativa. Le richieste saranno gestite nei termini previsti dalla normativa applicabile.",

    authority:
      "Se ritieni che il trattamento dei tuoi dati personali violi la normativa applicabile, puoi presentare reclamo al Garante per la protezione dei dati personali.",

    cookies:
      "Il sito utilizza strumenti tecnici necessari al proprio funzionamento e alla sicurezza. La preferenza della lingua viene salvata nella memoria locale del browser. La chat usa un token temporaneo per mantenere il contesto della conversazione, con scadenza di 30 minuti. Il sito non incorpora mappe o contenuti social: i collegamenti a servizi esterni, come Google Maps, Instagram o Facebook, trasmettono dati al relativo servizio quando li apri. Non utilizziamo i dati raccolti tramite il sito per profilazione pubblicitaria. Se verranno introdotti strumenti di analytics, advertising, pixel o tecnologie che richiedono consenso, l'informativa sarà aggiornata.",

    updates:
      "Questa informativa può essere aggiornata quando cambiano i servizi utilizzati, le modalità di trattamento o gli obblighi normativi. La data dell'ultimo aggiornamento è indicata all'inizio della pagina.",

    writeTo: "Email per richieste privacy",
    vat: "P.IVA",
    office: "sede in",
    back: "← Torna al sito",
  },

  en: {
    title: "Privacy Policy",
    updated: "Last updated: 17 October 2026",

    sections: {
      controller: "1. Data controller",
      data: "2. Personal data we process",
      purposes: "3. Purposes and legal bases",
      required: "4. Provision of data",
      retention: "5. Data retention",
      providers: "6. Recipients and technical providers",
      transfers: "7. International data transfers",
      security: "8. Security",
      rights: "9. Your rights",
      authority: "10. Complaints",
      cookies: "11. Cookies and technical tools",
      updates: "12. Changes to this policy",
    },

    controller:
      "The Data Controller operates the Makai Grand Line venue. The appointed Data Protection Officer (DPO) is Alessio Esposito and can be contacted at the email address shown above.",

    dataIntro:
      "When you use the website, make an online booking, call the venue or contact our staff regarding a booking, we may process the following data:",

    dataItems: [
      "the name provided for the booking;",
      "telephone number;",
      "email address, when provided or required for booking communications;",
      "booking date and time;",
      "number of guests;",
      "table assigned, where applicable;",
      "notes and requests included with the booking;",
      "booking status, including changes, cancellations and no-shows;",
      "information concerning service communications relating to the booking;",
      "change or cancellation requests, staff decisions and reconfirmations received through the personal link;",
      "messages sent to the Nostromo chatbot and information entered during the conversation; temporary chat context is transmitted in a signed token and expires after 30 minutes;",
      "waiting-list requests, including name, telephone number, email if provided, date, time, party size, notes, status and change history;",
      "service-communication data, such as recipient, channel, prepared content, sending status, provider identifiers and any errors;",
      "IP address and technical data used temporarily to limit abuse and protect the service;",
      "website language preference, stored in the browser's local storage;",
      "technical data strictly necessary for the operation and security of the service.",
    ],

    sensitive:
      "Please do not include health information or other particularly sensitive information in booking notes unless strictly necessary and after contacting the venue directly.",

    marketingData:
      "If you voluntarily choose to receive promotional communications, we also process the information required to document your consent, such as its date, channel, status and any subsequent withdrawal.",

    purposes: [
      {
        title: "Booking management",
        text: "We use your data to register and manage your booking, check availability, assign a table, handle changes or cancellations and contact you when necessary. The Nostromo chatbot may be used to answer requests and start a booking; its context is temporary. Legal basis for booking management: steps taken at your request or performance of the requested service under Article 6(1)(b) GDPR.",
      },
      {
        title: "Service communications",
        text: "We may send communications strictly related to your booking, such as confirmations, updates, reminders or operational messages. Booking confirmation emails may be sent automatically. The personal link lets you reconfirm, change or cancel your booking. Available changes and cancellations take effect immediately; when a change is unavailable, the booking stays unchanged and staff receive a request. The link expires 30 days after the booking and should not be shared. These communications are not marketing and are required for booking management.",
      },
      {
        title: "Operational management and booking history",
        text: "Information concerning bookings, waiting-list requests, changes, cancellations, arrivals, no-shows and relevant communications may be used by authorised staff to manage the service and reconstruct relevant operational events. Communications may be recorded together with their technical sending status.",
      },
      {
        title: "Marketing and promotions",
        text: "Promotional communications by email, WhatsApp or other channels are sent only where you have provided specific optional consent. Legal basis: consent under Article 6(1)(a) GDPR. Consent may be withdrawn at any time without affecting your booking.",
      },
    ],

    required:
      "Providing the data necessary for a booking is required in order for us to manage and confirm it. Marketing consent is optional, separate from the booking and is never required in order to use Makai's services.",

    retention: [
      "Bookings and related operational data — including DOPOCENA requests, customer requests, waiting-list entries and history, booking history, tokens, technical receipts and communication logs — are automatically deleted 30 days after the service or request date.",
      "Temporary Nostromo chatbot context expires after 30 minutes. Messages are not stored as a chat history in the database; if the conversation leads to a booking, the necessary data is recorded in the booking.",
      "Data relating to marketing consent and promotional activities are retained for up to 12 months from consent registration or renewal. Withdrawal immediately stops promotional use; proof of consent is retained for no more than 12 months from registration or renewal.",
      "Certain information may be retained longer where necessary to comply with legal obligations or establish or defend legal claims, in accordance with the principles of necessity and data minimisation.",
    ],

    providersIntro:
      "Data may be processed by authorised Makai staff and by technical providers necessary to operate the service. The main services currently used include:",

    providers: [
      "Supabase, for database, authentication and backend services;",
      "Vercel, for hosting and delivery of the website and backend services;",
      "Resend, for sending booking-related emails.",
      "WhatsApp/Meta, when you choose to contact the venue through WhatsApp or, if you have consented, to receive promotional communications through that channel.",
    ],

    providersOutro:
      "Providers process data according to their respective roles, contractual terms and applicable data protection obligations. Makai does not sell users' personal data to third parties.",

    transfers:
      "Some technology providers may use infrastructure or subprocessors located outside the European Economic Area. Where applicable, such transfers are carried out in accordance with the GDPR through adequacy decisions or other safeguards recognised by applicable law, including Standard Contractual Clauses.",

    security:
      "We adopt technical and organisational measures designed to protect personal data against unauthorised access, loss, alteration or improper disclosure. Administrative and management functions are restricted to authorised staff and backend services use authentication and authorisation controls.",

    rightsIntro:
      "Where provided for under the GDPR, you may exercise the following rights:",

    rights: [
      "access to your personal data;",
      "rectification of inaccurate data;",
      "erasure of your data;",
      "restriction of processing;",
      "data portability, where applicable;",
      "objection to processing, where applicable;",
      "withdrawal of consent at any time, without affecting the lawfulness of processing carried out before withdrawal.",
    ],

    rightsContact:
      "To exercise your rights, you may write to the email address indicated in this policy. Requests will be handled within the time limits established by applicable law.",

    authority:
      "If you believe that the processing of your personal data infringes applicable data protection law, you may lodge a complaint with the Italian Data Protection Authority (Garante per la protezione dei dati personali).",

    cookies:
      "The website uses technical tools required for its operation and security. Your language preference is saved in the browser's local storage. The chatbot uses a temporary token to maintain conversation context, which expires after 30 minutes. The website does not embed maps or social content: links to external services such as Google Maps, Instagram or Facebook send data to the relevant service when opened. We do not use website data for advertising profiling. If analytics, advertising tools, pixels or other technologies requiring consent are introduced, this policy will be updated.",

    updates:
      "This policy may be updated when the services we use, our processing activities or applicable legal requirements change. The date of the latest update is shown at the top of this page.",

    writeTo: "Privacy requests",
    vat: "VAT number",
    office: "registered office at",
    back: "← Back to the website",
  },
};

export default function Privacy() {
  const { language } = useLanguage();
  const copy = privacyCopy[language] || privacyCopy.it;

  return (
    <div className="scroll-container privacy-page">
      <SiteNav />

      <main className="privacy-main">
        <div className="privacy-card">
          <SiteHeading as="h1" className="privacy-title">{copy.title}</SiteHeading>
          <p className="privacy-updated">{copy.updated}</p>

          <h2>{copy.sections.controller}</h2>
          <p>
            <strong>{ragioneSociale}</strong>, {copy.vat} {piva}, {copy.office}{" "}
            {indirizzo}. {copy.controller}
          </p>
          <p>
            <strong>{copy.writeTo}:</strong> {emailPrivacy}
          </p>

          <h2>{copy.sections.data}</h2>
          <p>{copy.dataIntro}</p>
          <ul>
            {copy.dataItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>{copy.sensitive}</p>
          <p>{copy.marketingData}</p>

          <h2>{copy.sections.purposes}</h2>
          {copy.purposes.map((purpose) => (
            <p key={purpose.title}>
              <strong>{purpose.title}.</strong> {purpose.text}
            </p>
          ))}

          <h2>{copy.sections.required}</h2>
          <p>{copy.required}</p>

          <h2>{copy.sections.retention}</h2>
          <ul>
            {copy.retention.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h2>{copy.sections.providers}</h2>
          <p>{copy.providersIntro}</p>
          <ul>
            {copy.providers.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>{copy.providersOutro}</p>

          <h2>{copy.sections.transfers}</h2>
          <p>{copy.transfers}</p>

          <h2>{copy.sections.security}</h2>
          <p>{copy.security}</p>

          <h2>{copy.sections.rights}</h2>
          <p>{copy.rightsIntro}</p>
          <ul>
            {copy.rights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>
            {copy.rightsContact} <strong>{emailPrivacy}</strong>
          </p>

          <h2>{copy.sections.authority}</h2>
          <p>{copy.authority}</p>

          <h2>{copy.sections.cookies}</h2>
          <p>{copy.cookies}</p>

          <h2>{copy.sections.updates}</h2>
          <p>{copy.updates}</p>

          <a className="privacy-back" href="/">
            {copy.back}
          </a>
        </div>
      </main>
    </div>
  );
}
