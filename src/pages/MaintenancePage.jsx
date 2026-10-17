import { contactInfo } from "../data/contactInfo";
import SiteHeading from "../components/SiteHeading";

export default function MaintenancePage() {
  return <main className="maintenance-page" aria-labelledby="maintenance-title">
    <div className="maintenance-card">
      <img className="maintenance-logo"
        src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.webp`}
        alt="Makai Grand Line" width="520" height="174" />
      <p className="maintenance-eyebrow">Una breve sosta in porto</p>
      <SiteHeading as="h1" id="maintenance-title" className="maintenance-title">La ciurma Makai è ai lavori!</SiteHeading>
      <p className="maintenance-message">Stiamo migliorando il nostro sistema di prenotazioni per offrirvi un'esperienza ancora migliore. Le prenotazioni online sono temporaneamente sospese. Torneremo presto operativi!</p>
      <div className="maintenance-contact" aria-label="Contatti Makai">
        <a href={contactInfo.whatsappHref} target="_blank" rel="noreferrer">Scrivici su WhatsApp</a>
        <a href={contactInfo.phoneHref}>Chiama {contactInfo.phoneDisplay}</a>
        <a href={`mailto:${contactInfo.email}`}>{contactInfo.email}</a>
      </div>
      <p className="maintenance-address">{contactInfo.address}</p>
      <a className="maintenance-privacy" href="/privacy">Privacy</a>
    </div>
  </main>;
}
