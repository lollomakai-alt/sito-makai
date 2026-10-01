import { useLanguage } from "../i18n/LanguageContext";

export default function LanguageSwitcher({ className = "" }) {
  const { language, setLanguage } = useLanguage();

  return (
    <div className={`lang-control ${className}`.trim()} aria-label="Language">
      <button className={`lang ${language === "it" ? "active" : ""}`} type="button" lang="it" aria-pressed={language === "it"} onClick={() => setLanguage("it")}>IT</button>
      <span aria-hidden="true">|</span>
      <button className={`lang ${language === "en" ? "active" : ""}`} type="button" lang="en" aria-pressed={language === "en"} onClick={() => setLanguage("en")}>EN</button>
    </div>
  );
}
