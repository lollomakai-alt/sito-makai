export default function AboutSection() {
  return (
    <section id="chi-siamo" className="about-section content-section" aria-labelledby="about-title">
      <h2 id="about-title" className="about-title">Chi siamo</h2>
      <div className="about-panel">
        <div className="about-subtitle-container">
          <p className="about-subtitle">La nostra rotta, il vostro approdo
            <br />
            Makai nasce dall’incontro tra l’anima Tiki e lo spirito dell’avventura.
            Un luogo dove cocktail, sapori esotici e atmosfere piratesche vi
            invitano a lasciare la quotidianità a terra.
            Salite a bordo: il viaggio comincia qui.
          </p>
        </div>
      </div>
      <div className="about-photos">
        <img
          src={`${import.meta.env.BASE_URL}images/chi-siamo.png`}
          alt="Foto della sezione Chi siamo"
          width="816"
          height="980"
          loading="lazy"
          decoding="async"
        />
        <img
          src={`${import.meta.env.BASE_URL}images/statua.JPG`}
          alt="Statua del Makai"
          width="896"
          height="1195"
          loading="lazy"
          decoding="async"
        />
      </div>
      <a className="about-more-link" href="/chi-siamo">
        Scopri di più <span aria-hidden="true">→</span>
      </a>
    </section>
  );
}
