import { useEffect, useRef, useState } from "react";
import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "./LanguageSwitcher";

const navItems = [
  { label: "about", id: "chi-siamo" },
  { label: "menu", id: "menu" },
  { label: "events", id: "eventi" },
  { label: "gallery", id: "galleria", href: "/galleria" },
  { label: "contacts", id: "contatti" },
];

export default function SiteNav({ activeSection }) {
  const { language } = useLanguage();
  const copy = siteCopy[language].nav;
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navRef = useRef(null);
  const toggleRef = useRef(null);

  useEffect(() => {
    const mobileQuery = window.matchMedia("(max-width: 768px)");

    const closeOnDesktop = (event) => {
      if (!event.matches) setIsMenuOpen(false);
    };

    const closeOnOutsideClick = (event) => {
      if (isMenuOpen && !navRef.current?.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };

    const closeOnEscape = (event) => {
      if (event.key === "Escape" && isMenuOpen) {
        setIsMenuOpen(false);
        toggleRef.current?.focus();
      }
    };

    mobileQuery.addEventListener("change", closeOnDesktop);
    document.addEventListener("pointerdown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);

    return () => {
      mobileQuery.removeEventListener("change", closeOnDesktop);
      document.removeEventListener("pointerdown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isMenuOpen]);

  return (
    <nav ref={navRef} className="top-nav" aria-label={copy.label}>
      <a
        href="/#hero"
        className="brand"
      >
        <img
          src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.PNG`}
          alt="Makai Grand Line"
          className="logo-full"
        />
      </a>

      <button
        ref={toggleRef}
        className={`mobile-nav-toggle ${isMenuOpen ? "is-open" : ""}`}
        type="button"
        aria-label={isMenuOpen ? copy.close : copy.open}
        aria-controls="site-navigation-links"
        aria-expanded={isMenuOpen}
        onClick={() => setIsMenuOpen((isOpen) => !isOpen)}
      >
        <span />
        <span />
        <span />
      </button>

      <div
        id="site-navigation-links"
        className={`nav-links ${isMenuOpen ? "is-open" : ""}`}
      >
        {navItems.map((item) => (
          <a
            key={item.id}
            href={item.href || `/#${item.id}`}
            className={`nav-item ${activeSection === item.label ? "active" : ""}`}
            aria-current={activeSection === item.label ? "location" : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            {copy[item.label]}
          </a>
        ))}
      </div>
      <LanguageSwitcher />
    </nav>
  );
}
