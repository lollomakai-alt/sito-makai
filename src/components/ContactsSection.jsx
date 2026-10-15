import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";
import { contactInfo } from "../data/contactInfo";
import HomeSectionHeading from "./HomeSectionHeading";

const mapsUrl = "https://www.google.com/maps/place//data=!4m2!3m1!1s0x132f602bc97659d1:0x91e31e79d05bc2c6?sa=X&ved=1t:8290&ictx=111";

export default function ContactsSection() {
  const { language } = useLanguage();
  const copy = siteCopy[language].contacts;

  return (
    <section id="contatti" className="contacts-section content-section" aria-labelledby="contacts-title">
      <HomeSectionHeading id="contacts-title" className="contacts-title">{copy.title}</HomeSectionHeading>
      <div className="contacts-layout">
        <div className="contacts-totem" aria-hidden="true">
          <img
            src={`${import.meta.env.BASE_URL}images/logo/logo-totem.webp`}
            alt=""
            width="520"
            height="998"
            loading="lazy"
            decoding="async"
          />
        </div>

        <div className="contacts-content">
          <address className="contacts-panel">
            <div className="contact-item">
              <span className="contact-label">{copy.address}</span>
              <a href={mapsUrl} target="_blank" rel="noreferrer">
                {contactInfo.address}
              </a>
              <a className="maps-link" href={mapsUrl} target="_blank" rel="noreferrer">
                {copy.maps}
              </a>
            </div>
            <div className="contact-item">
              <span className="contact-label">{copy.phone}</span>
              <a href={contactInfo.phoneHref}>{contactInfo.phoneDisplay}</a>
            </div>
            <div className="contact-item">
              <span className="contact-label">{copy.email}</span>
              <a href={`mailto:${contactInfo.email}`}>{contactInfo.email}</a>
            </div>
          </address>
          <a className="contacts-booking-button" href="/prenotazioni">
            {copy.booking}
          </a>
          <div className="social-links" aria-label={copy.socialLabel}>
            <a href={contactInfo.whatsappHref} target="_blank" rel="noreferrer">
              WhatsApp
            </a>
            <a href="https://www.instagram.com/makai_pigneto/" target="_blank" rel="noreferrer">
              Instagram
            </a>
            <a href="https://www.facebook.com/MakaiSurfAndTikiBar" target="_blank" rel="noreferrer">
              Facebook
            </a>
            <a className="privacy-link" href="/privacy">Privacy</a>
          </div>
        </div>
      </div>
    </section>
  );
}
