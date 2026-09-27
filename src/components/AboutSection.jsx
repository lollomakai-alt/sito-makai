export default function AboutSection() {
  return (
    <section id="chi-siamo" className="about-section content-section" aria-labelledby="about-title">
      <h2 id="about-title" className="about-title">Chi siamo</h2>
      <div className="about-photos">
        <img
          src={`${import.meta.env.BASE_URL}images/totem.PNG`}
          alt="Totem del Makai"
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
      <p className="about-subtitle">La nostra rotta, il vostro approdo</p>
      <div className="about-description">
        <p>
          Makai nasce dall’incontro tra l’anima Tiki e lo spirito dell’avventura.
          Un luogo dove cocktail, sapori esotici e atmosfere piratesche vi
          invitano a lasciare la quotidianità a terra.
        </p>
        <p>Salite a bordo: il viaggio comincia qui.</p>
      </div>
    </section>
  );
}
