import SiteNav from "../components/SiteNav";
import { useLanguage } from "../i18n/LanguageContext";

const ragioneSociale = "AMACA S.r.l.";
const piva = "13934581003";
const indirizzo = "Via dei Magazzini Generali 4, 00154 Roma";
const emailPrivacy = "makairoma@gmail.com";

const privacyCopy = {
  it: {
    title: "Informativa sulla privacy",
    updated: "Ultimo aggiornamento: 6 ottobre 2026",

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
      "Il Titolare del trattamento gestisce il locale Makai Grand Line. Per qualsiasi richiesta relativa alla protezione dei dati personali puoi utilizzare l'indirizzo email indicato sopra.",

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
      "dati tecnici strettamente necessari al funzionamento e alla sicurezza del servizio.",
    ],

    sensitive:
      "Ti chiediamo di non inserire nelle note dati relativi alla salute o altre informazioni particolarmente sensibili, salvo quando strettamente necessario e dopo aver contattato direttamente il locale.",

    marketingData:
      "Se scegli volontariamente di ricevere comunicazioni promozionali, trattiamo inoltre i dati necessari a documentare il consenso, come data, canale, stato del consenso ed eventuale revoca.",

    purposes: [
      {
        title: "Gestione della prenotazione",
        text: "Utilizziamo i dati per registrare e gestire la prenotazione, verificare la disponibilità, assegnare il tavolo, gestire eventuali modifiche o cancellazioni e contattarti quando necessario. Base giuridica: esecuzione di misure precontrattuali o del servizio richiesto, ai sensi dell'art. 6, par. 1, lett. b) GDPR.",
      },
      {
        title: "Comunicazioni di servizio",
        text: "Possiamo inviarti comunicazioni strettamente collegate alla prenotazione, come conferme, aggiornamenti, promemoria o comunicazioni operative. Le email di conferma possono essere inviate automaticamente. Queste comunicazioni non costituiscono marketing e sono funzionali alla gestione della prenotazione.",
      },
      {
        title: "Gestione operativa e storico delle prenotazioni",
        text: "Le informazioni relative a prenotazioni, modifiche, cancellazioni, arrivi, mancata presentazione e comunicazioni rilevanti possono essere utilizzate dal personale autorizzato per gestire il servizio e ricostruire gli eventi operativi collegati alla prenotazione.",
      },
      {
        title: "Marketing e promozioni",
        text: "Comunicazioni promozionali tramite email, WhatsApp o altri canali vengono effettuate solo in presenza di uno specifico consenso facoltativo. Base giuridica: consenso, ai sensi dell'art. 6, par. 1, lett. a) GDPR. Il consenso può essere revocato in qualsiasi momento senza conseguenze sulla prenotazione.",
      },
    ],

    required:
      "Il conferimento dei dati necessari alla prenotazione è indispensabile per poterla gestire e confermare. Il consenso per finalità di marketing è invece facoltativo, separato dalla prenotazione e non è mai necessario per utilizzare i servizi del Makai.",

    retention: [
      "I dati della prenotazione vengono conservati per il periodo necessario alla gestione del servizio e secondo le scadenze configurate nei sistemi Makai.",
      "In assenza del consenso a essere ricordato per prenotazioni future, il sistema prevede una scadenza ordinaria dei dati personali della prenotazione dopo 30 giorni.",
      "Quando è presente il consenso a essere ricordato per prenotazioni future, il sistema prevede una conservazione fino a 12 mesi.",
      "I dati relativi al consenso marketing e alle attività promozionali possono essere conservati fino a 24 mesi dal consenso, salvo revoca precedente.",
      "Alcune informazioni possono essere conservate più a lungo quando ciò sia necessario per adempiere a obblighi di legge, tutelare un diritto o documentare eventi rilevanti, nel rispetto dei principi di necessità e minimizzazione.",
    ],

    providersIntro:
      "I dati possono essere trattati dal personale autorizzato del Makai e dai fornitori tecnici necessari al funzionamento del servizio. Tra i principali servizi utilizzati:",

    providers: [
      "Supabase, per database, autenticazione e servizi backend;",
      "Vercel, per hosting e distribuzione del sito web;",
      "Resend, per l'invio delle email relative alle prenotazioni.",
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
      "Il sito utilizza strumenti tecnici necessari al proprio funzionamento e alla sicurezza del servizio. Non utilizziamo i dati raccolti tramite il sito per attività di profilazione pubblicitaria. Qualora in futuro vengano introdotti strumenti di analytics, advertising, pixel o tecnologie che richiedano consenso, la gestione dei cookie e questa informativa verranno aggiornate di conseguenza.",

    updates:
      "Questa informativa può essere aggiornata quando cambiano i servizi utilizzati, le modalità di trattamento o gli obblighi normativi. La data dell'ultimo aggiornamento è indicata all'inizio della pagina.",

    writeTo: "Email per richieste privacy",
    vat: "P.IVA",
    office: "sede in",
    back: "← Torna al sito",
  },

  en: {
    title: "Privacy Policy",
    updated: "Last updated: 6 October 2026",

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
      "The Data Controller operates the Makai Grand Line venue. For any request concerning the protection of personal data, you may use the email address shown above.",

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
      "technical data strictly necessary for the operation and security of the service.",
    ],

    sensitive:
      "Please do not include health information or other particularly sensitive information in booking notes unless strictly necessary and after contacting the venue directly.",

    marketingData:
      "If you voluntarily choose to receive promotional communications, we also process the information required to document your consent, such as its date, channel, status and any subsequent withdrawal.",

    purposes: [
      {
        title: "Booking management",
        text: "We use your data to register and manage your booking, check availability, assign a table, handle changes or cancellations and contact you when necessary. Legal basis: steps taken at your request or performance of the requested service under Article 6(1)(b) GDPR.",
      },
      {
        title: "Service communications",
        text: "We may send communications strictly related to your booking, such as confirmations, updates, reminders or operational messages. Booking confirmation emails may be sent automatically. These communications are not marketing and are required for booking management.",
      },
      {
        title: "Operational management and booking history",
        text: "Information concerning bookings, changes, cancellations, arrivals, no-shows and relevant communications may be used by authorised staff to manage the service and reconstruct relevant operational events associated with a booking.",
      },
      {
        title: "Marketing and promotions",
        text: "Promotional communications by email, WhatsApp or other channels are sent only where you have provided specific optional consent. Legal basis: consent under Article 6(1)(a) GDPR. Consent may be withdrawn at any time without affecting your booking.",
      },
    ],

    required:
      "Providing the data necessary for a booking is required in order for us to manage and confirm it. Marketing consent is optional, separate from the booking and is never required in order to use Makai's services.",

    retention: [
      "Booking data is retained for the period necessary to manage the service and according to the retention periods configured in Makai's systems.",
      "Without consent to remember your details for future bookings, the system provides for an ordinary expiry of personal booking data after 30 days.",
      "Where consent to remember your details for future bookings has been provided, data may be retained for up to 12 months.",
      "Data relating to marketing consent and promotional activities may be retained for up to 24 months from the date of consent, unless consent is withdrawn earlier.",
      "Certain information may be retained for longer where necessary to comply with legal obligations, establish or defend legal claims, or document relevant events, in accordance with the principles of necessity and data minimisation.",
    ],

    providersIntro:
      "Data may be processed by authorised Makai staff and by technical providers necessary to operate the service. The main services currently used include:",

    providers: [
      "Supabase, for database, authentication and backend services;",
      "Vercel, for website hosting and delivery;",
      "Resend, for sending booking-related emails.",
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
      "The website uses technical tools required for its operation and security. We do not use information collected through the website for advertising profiling. If analytics, advertising tools, pixels or other technologies requiring consent are introduced in the future, cookie management and this policy will be updated accordingly.",

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
          <h1>{copy.title}</h1>
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
