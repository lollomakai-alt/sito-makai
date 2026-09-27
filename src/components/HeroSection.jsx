export default function HeroSection() {
  return (
    <section id="hero" className="hero-section">
      <div className="hero-content">
        <h1 className="gold-text">Benvenuti a bordo del Makai</h1>
        <p className="hero-description">
          Un'esperienza immersiva dove l'anima Tiki e lo spirito dell'avventura
          si incontrano in un viaggio tra sapori esotici e atmosfere piratesche.
        </p>
        <img
          src={`${import.meta.env.BASE_URL}images/makai inizio.PNG`}
          alt="Interno del Makai"
          className="hero-main-img"
        />
      </div>
    </section>
  );
}
