import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";

const wallPhotos = [
  { src: "menu.webp" },
  { src: "drinktop.webp" },
  { src: "carne-osso.webp" },
  { src: "MENU56.webp" },
  { src: "panino.webp" },
  { src: "sushi.webp" },
  { src: "Udon di oden .webp" },
  { src: "sushi2.webp" },
];

const mobilePhotos = wallPhotos.slice(0, 4);

function prefersLightHero() {
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  return Boolean(
    connection?.saveData ||
    ["slow-2g", "2g"].includes(connection?.effectiveType) ||
    (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
    (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4),
  );
}

function HeroPhoto({ photo, eager = false }) {
  const base = import.meta.env.BASE_URL;
  const src = `${base}images/${encodeURIComponent(photo.src)}`;
  const mobileSrc = `${base}images/hero/mobile/${encodeURIComponent(photo.src)}`;
  const desktopSrc = `${base}images/hero/${encodeURIComponent(photo.src)}`;
  return (
    <figure className="hero-photo">
      <picture>
        <source media="(max-width: 767px)" srcSet={mobileSrc} type="image/webp" />
        <source srcSet={desktopSrc} type="image/webp" />
        <img
          src={src}
          alt=""
          loading={eager ? "eager" : "lazy"}
          fetchpriority={eager ? "high" : "low"}
          decoding="async"
          draggable={false}
        />
      </picture>
    </figure>
  );
}

function PhotoWall({ label }) {
  const [isMobile, setIsMobile] = useState(() => window.matchMedia("(max-width: 767px)").matches);
  const [lightHero, setLightHero] = useState(prefersLightHero);

  useEffect(() => {
    const mobileQuery = window.matchMedia("(max-width: 767px)");
    const updateProfile = () => {
      setIsMobile(mobileQuery.matches);
      setLightHero(prefersLightHero());
    };
    updateProfile();
    mobileQuery.addEventListener("change", updateProfile);
    return () => mobileQuery.removeEventListener("change", updateProfile);
  }, []);

  const photos = isMobile || lightHero ? mobilePhotos : wallPhotos;
  const isMovingWall = !isMobile && !lightHero;

  return (
    <div className={`hero-wall${isMovingWall ? " hero-wall-moving" : ""}`}>
      <div
        className="hero-wall-track"
        role="img"
        aria-label={label}
      >
        {photos.map((photo, index) => (
          <HeroPhoto key={photo.src} photo={photo} eager={index === 0} />
        ))}
        {isMovingWall && (
          <div className="hero-wall-copy" aria-hidden="true">
            {photos.map((photo) => <HeroPhoto key={photo.src} photo={photo} />)}
          </div>
        )}
      </div>
    </div>
  );
}

export default function HeroSection() {
  const { language } = useLanguage();
  const copy = siteCopy[language].hero;
  const sectionRef = useRef(null);

  useLayoutEffect(() => {
    const section = sectionRef.current;
    const nav = document.querySelector(".top-nav");
    if (!nav) return undefined;

    const reserveNavSpace = () => {
      section.style.setProperty("--hero-nav-height", `${nav.getBoundingClientRect().height}px`);
    };
    reserveNavSpace();
    const observer = new ResizeObserver(reserveNavSpace);
    observer.observe(nav);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} id="hero" className="hero-section" aria-labelledby="hero-title">
      <PhotoWall label={copy.wallLabel} />
      <div className="hero-content">
        <div className="hero-copy-panel">
          <p className="hero-kicker">{copy.eyebrow}</p>
          <h1 id="hero-title" className="hero-title">{copy.title}</h1>
          <div className="hero-divider" aria-hidden="true">
            <img
              src={`${import.meta.env.BASE_URL}images/hero/straw-hat-skull.svg`}
              alt=""
              width="54"
              height="42"
            />
          </div>
          <p className="hero-subtitle">{copy.description}</p>
        </div>
      </div>
    </section>
  );
}
