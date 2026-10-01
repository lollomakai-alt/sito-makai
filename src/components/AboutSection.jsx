import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";

export default function AboutSection() {
  const { language } = useLanguage();
  const copy = siteCopy[language].about;
  const [lead, body] = copy.text.split("\n");

  return (
    <section id="chi-siamo" className="about-section content-section" aria-labelledby="about-title">
      <h2 id="about-title" className="section-title">{copy.title}</h2>
      <a href="/chi-siamo" className="about-panel-link" aria-label={`${copy.more} — ${copy.title}`}>
        <div className="about-panel panel">
          <p className="section-subtitle">{lead}
            <br />
            {body}
          </p>
        </div>
      </a>
      <div className="about-photos">
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
  );
}
