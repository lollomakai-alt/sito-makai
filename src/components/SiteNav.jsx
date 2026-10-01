import { useEffect, useRef, useState } from "react";

const navItems = [
  { name: "Chi siamo", id: "chi-siamo" },
  { name: "Menu", id: "menu" },
  { name: "Eventi", id: "eventi" },
  { name: "Galleria", id: "galleria", href: "/galleria" },
  { name: "Contatti", id: "contatti" },
];

export default function SiteNav({ activeSection }) {
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
    <nav ref={navRef} className="top-nav" aria-label="Navigazione principale">
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
        aria-label={isMenuOpen ? "Chiudi il menu" : "Apri il menu"}
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
            className={`nav-item ${activeSection === item.name ? "active" : ""}`}
            aria-current={activeSection === item.name ? "location" : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            {item.name}
          </a>
        ))}
      </div>
      <div className="lang-control">
        <span className="lang active">IT</span> | <span className="lang">EN</span>
      </div>
    </nav>
  );
}
