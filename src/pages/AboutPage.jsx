import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

const aboutPageCopy = {
  it: {
    title: "La nostra rotta",
    paragraphs: [
      "Tutto è cominciato con un sogno, o forse con un rum versato al tramonto su una spiaggia lontana. Tre barman, tre amici, tre viaggiatori instancabili, uniti da una sola passione: il mondo Tiki.",
      "Tra corsi internazionali, cocktail bar d'oltreoceano e notti passate a respirare l'anima esotica di luoghi sperduti, è nata l'idea di portare il vero spirito Tiki in Italia non una copia, ma un'esperienza autentica, fatta di cultura, creatività e condivisione. Da quel sogno sono nati altri due luoghi, a Roma e a Fiumicino, prima di approdare qui.",
      "Oggi il Makai vive al Pigneto, e non è più solo un tempio Tiki: è salpato verso nuove rotte. Qui l'anima esotica della cultura polinesiana si fonde con lo spirito piratesco della Grand Line — un equipaggio di sapori, rum e avventura ispirato al mondo di One Piece. Cocktail iconici serviti in scenografici Tiki mug, un menù fusion che racconta isole lontane e ciurme leggendarie, musica dal vivo e un'atmosfera curata in ogni dettaglio: ogni angolo del locale è pensato per farvi sentire a bordo di una nave che ha lasciato il porto per non tornare più indietro.",
      "Non è solo un bar. Non è solo un ristorante. È un'isola, un equipaggio, una promessa di evasione. È la nostra casa… e ora, anche la tua.",
      "Salpate con noi. Benvenuti a bordo del Makai. 🏴‍☠️🌺🍍",
    ],
    imageOne: "Totem e arredi Tiki del Makai",
    imageTwo: "Statua decorativa del Makai",
  },
  en: {
    title: "Our route",
    paragraphs: [
      "It all began with a dream, or perhaps with a glass of rum poured at sunset on a distant beach. Three bartenders, three friends and three tireless travellers, united by one passion: the Tiki world.",
      "Between international courses, cocktail bars overseas and nights spent breathing in the exotic soul of faraway places, the idea was born to bring the true Tiki spirit to Italy: not a copy, but an authentic experience built on culture, creativity and sharing. That dream led to two other venues in Rome and Fiumicino before arriving here.",
      "Today Makai lives in Pigneto, and it is no longer only a Tiki temple: it has set sail for new routes. Here, the exotic soul of Polynesian culture meets the pirate spirit of the Grand Line, with a crew of flavours, rum and adventure inspired by One Piece. Iconic cocktails served in spectacular Tiki mugs, a fusion menu telling stories of distant islands and legendary crews, live music and an atmosphere shaped down to the smallest detail: every corner is designed to make you feel aboard a ship that has left port without looking back.",
      "It is more than a bar. It is more than a restaurant. It is an island, a crew and a promise of escape. It is our home… and now it is yours too.",
      "Set sail with us. Welcome aboard Makai. 🏴‍☠️🌺🍍",
    ],
    imageOne: "Makai Tiki totem and décor",
    imageTwo: "Makai decorative statue",
  },
};

export default function AboutPage({ containerRef }) {
  const { language } = useLanguage();
  const common = siteCopy[language].common;
  const copy = aboutPageCopy[language];
  const paragraphStyle = { color: "#ffffff", fontFamily: "Georgia, serif", lineHeight: "1.7", fontSize: "1.1rem" };

  return (
    <div ref={containerRef} className="scroll-container about-detail-page">
      <header className="about-detail-header">
        <a href="/" className="brand" aria-label={common.brandHome}>
          <img
            src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.PNG`}
            alt="Makai Grand Line"
            className="logo-full"
          />
        </a>
        <div className="detail-header-actions">
          <a href="/" className="about-detail-back">{common.backShort}</a>
          <LanguageSwitcher className="detail-language" />
        </div>
      </header>

      <main className="about-detail-main">
        <section className="about-detail-section content-section" aria-labelledby="about-detail-title">
          <h1 id="about-detail-title" className="about-title">{copy.title}</h1>
          
          {/* Stile applicato direttamente per testo bianco e font Georgia più leggibile */}
          <div className="about-detail-copy" style={{ color: '#ffffff', fontFamily: 'Georgia, serif' }}>
            {copy.paragraphs.map((paragraph) => <p key={paragraph} style={paragraphStyle}>{paragraph}</p>)}
          </div>

          <div className="about-detail-photos">
            <img
              src={`${import.meta.env.BASE_URL}images/chi-siamo.webp`}
              alt={copy.imageOne}
              width="816"
              height="980"
              loading="lazy"
              decoding="async"
            />
            <img
              src={`${import.meta.env.BASE_URL}images/statua.webp`}
              alt={copy.imageTwo}
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
