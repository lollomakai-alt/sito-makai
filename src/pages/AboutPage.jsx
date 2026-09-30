export default function AboutPage({ containerRef }) {
  return (
    <div ref={containerRef} className="scroll-container about-detail-page">
      <header className="about-detail-header">
        <a href="/" className="brand" aria-label="Torna alla homepage Makai">
          <img
            src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.PNG`}
            alt="Makai Grand Line"
            className="logo-full"
          />
        </a>
        <a href="/" className="about-detail-back">← Torna alla home</a>
      </header>

      <main className="about-detail-main">
        <section className="about-detail-section content-section" aria-labelledby="about-detail-title">
          <h1 id="about-detail-title" className="about-title">La nostra rotta</h1>
          
          {/* Stile applicato direttamente per testo bianco e font Georgia più leggibile */}
          <div className="about-detail-copy" style={{ color: '#ffffff', fontFamily: 'Georgia, serif' }}>
            <p style={{ color: '#ffffff', fontFamily: 'Georgia, serif', lineHeight: '1.7', fontSize: '1.1rem' }}>
              Tutto è cominciato con un sogno, o forse con un rum versato al
              tramonto su una spiaggia lontana. Tre barman, tre amici, tre
              viaggiatori instancabili, uniti da una sola passione: il mondo Tiki.
            </p>
            <p style={{ color: '#ffffff', fontFamily: 'Georgia, serif', lineHeight: '1.7', fontSize: '1.1rem' }}>
              Tra corsi internazionali, cocktail bar d'oltreoceano e notti
              passate a respirare l'anima esotica di luoghi sperduti, è nata
              l'idea di portare il vero spirito Tiki in Italia non una copia,
              ma un'esperienza autentica, fatta di cultura, creatività e
              condivisione. Da quel sogno sono nati altri due luoghi, a Roma e a
              Fiumicino, prima di approdare qui.
            </p>
            <p style={{ color: '#ffffff', fontFamily: 'Georgia, serif', lineHeight: '1.7', fontSize: '1.1rem' }}>
              Oggi il Makai vive al Pigneto, e non è più solo un tempio Tiki: è
              salpato verso nuove rotte. Qui l'anima esotica della cultura
              polinesiana si fonde con lo spirito piratesco della Grand Line — un
              equipaggio di sapori, rum e avventura ispirato al mondo di One
              Piece. Cocktail iconici serviti in scenografici Tiki mug, un menù
              fusion che racconta isole lontane e ciurme leggendarie, musica dal
              vivo e un'atmosfera curata in ogni dettaglio: ogni angolo del
              locale è pensato per farvi sentire a bordo di una nave che ha
              lasciato il porto per non tornare più indietro.
            </p>
            <p style={{ color: '#ffffff', fontFamily: 'Georgia, serif', lineHeight: '1.7', fontSize: '1.1rem' }}>
              Non è solo un bar. Non è solo un ristorante.
              <br />
              È un'isola, un equipaggio, una promessa di evasione.
              <br />
              È la nostra casa… e ora, anche la tua.
            </p>
            <p style={{ color: '#ffffff', fontFamily: 'Georgia, serif', lineHeight: '1.7', fontSize: '1.1rem' }}>
              Salpate con noi. Benvenuti a bordo del Makai. 🏴‍☠️🌺🍍
            </p>
          </div>

          <div className="about-detail-photos">
            <img
              src={`${import.meta.env.BASE_URL}images/chi-siamo.webp`}
              alt="Totem e arredi Tiki del Makai"
              width="816"
              height="980"
              loading="lazy"
              decoding="async"
            />
            <img
              src={`${import.meta.env.BASE_URL}images/statua.webp`}
              alt="Statua decorativa del Makai"
              width="896"
              height="1195"
              loading="lazy"
              decoding="async"
            />
          </div>
        </section>
      </main>
    </div>
  );
}
