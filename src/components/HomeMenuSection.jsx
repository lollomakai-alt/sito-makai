import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";

export default function HomeMenuSection() {
  const { language } = useLanguage();
  const copy = siteCopy[language].homeMenu;

  return (
    <section id="menu" className="menu-section content-section" aria-labelledby="menu-title">
      <h2 id="menu-title" className="menu-title">{copy.title}</h2>
      <div className="menu-panels">
        <a className="menu-panel" href="/menu-drink">
          <div className="menu-panel-copy">
            <h3>{copy.drinkTitle}</h3>
            <p>{copy.drinkText}</p>
          </div>
          <img
            src={`${import.meta.env.BASE_URL}images/drinktop.webp`}
            alt={copy.drinkAlt}
            width="1179"
            height="1592"
            loading="lazy"
            decoding="async"
          />
        </a>

        <a className="menu-panel" href="/menu-food">
          <div className="menu-panel-copy">
            <h3>{copy.foodTitle}</h3>
            <p>{copy.foodText}</p>
          </div>
          <img
            src={`${import.meta.env.BASE_URL}images/menutop.webp`}
            alt={copy.foodAlt}
            width="1179"
            height="1561"
            loading="lazy"
            decoding="async"
          />
        </a>
      </div>
    </section>
  );
}
