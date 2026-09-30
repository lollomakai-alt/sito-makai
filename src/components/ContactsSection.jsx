const mapsUrl = "https://www.google.com/maps/place//data=!4m2!3m1!1s0x132f602bc97659d1:0x91e31e79d05bc2c6?sa=X&ved=1t:8290&ictx=111";

export default function ContactsSection({ onOpenChat }) {
  return (
    <section id="contatti" className="contacts-section content-section" aria-labelledby="contacts-title">
      <h2 id="contacts-title" className="contacts-title">Contatti</h2>
      <div className="contacts-layout">
        <div className="contacts-totem" aria-hidden="true">
          <img
            src={`${import.meta.env.BASE_URL}images/logo/logo-totem.png`}
            alt=""
            width="466"
            height="894"
            loading="lazy"
            decoding="async"
          />
        </div>

        <div className="contacts-content">
          <address className="contacts-panel">
            <div className="contact-item">
              <span className="contact-label">Indirizzo</span>
              <a href={mapsUrl} target="_blank" rel="noreferrer">
                Via Braccio da Montone, 3/B, 00100 Roma RM
              </a>
              <a className="maps-link" href={mapsUrl} target="_blank" rel="noreferrer">
                Apri su Google Maps ↗
              </a>
            </div>
            <div className="contact-item">
              <span className="contact-label">Telefono</span>
              <a href="tel:+393397514140">339 751 4140</a>
            </div>
            <div className="contact-item">
              <span className="contact-label">Email</span>
              <a href="mailto:makairoma@gmail.com">makairoma@gmail.com</a>
            </div>
          </address>
          <button type="button" className="contacts-booking-button" onClick={onOpenChat}>
            Prenota qui
          </button>
          <div className="social-links" aria-label="Profili social e WhatsApp">
            <a href="https://wa.me/393397514140" target="_blank" rel="noreferrer">
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
