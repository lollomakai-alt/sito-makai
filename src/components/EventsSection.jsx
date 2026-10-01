import { useEffect, useRef, useState } from "react";
import { eventImages } from "virtual:event-images";
import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";

export default function EventsSection() {
  const { language } = useLanguage();
  const copy = siteCopy[language].events;
  const galleryRef = useRef(null);
  const [isGalleryPaused, setIsGalleryPaused] = useState(false);

  useEffect(() => {
    if (isGalleryPaused) return undefined;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let intervalId;
    const updateAutoplay = () => {
      window.clearInterval(intervalId);
      if (reducedMotion.matches) return;
      intervalId = window.setInterval(() => {
        const gallery = galleryRef.current;
        if (!gallery || !gallery.clientWidth || !gallery.children.length) return;
        const currentIndex = Math.round(gallery.scrollLeft / gallery.clientWidth);
        const nextIndex = (currentIndex + 1) % gallery.children.length;
        gallery.scrollTo({ left: nextIndex * gallery.clientWidth, behavior: "smooth" });
      }, 3500);
    };
    updateAutoplay();
    reducedMotion.addEventListener("change", updateAutoplay);
    return () => {
      window.clearInterval(intervalId);
      reducedMotion.removeEventListener("change", updateAutoplay);
    };
  }, [isGalleryPaused]);

  const scrollGallery = (direction) => {
    const gallery = galleryRef.current;
    if (!gallery) return;

    gallery.scrollBy({
      left: direction * gallery.clientWidth,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
    });
  };

  return (
    <section id="eventi" className="events-section content-section" aria-labelledby="events-title">
      <h2 id="events-title" className="events-title">{copy.title}</h2>
      <div className="events-layout">
        <div className="events-copy">
          <p>{copy.text}</p>
        </div>

        <div
          className="events-gallery-panel"
          onMouseEnter={() => setIsGalleryPaused(true)}
          onMouseLeave={() => setIsGalleryPaused(false)}
          onFocus={() => setIsGalleryPaused(true)}
          onBlur={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) {
              setIsGalleryPaused(false);
            }
          }}
        >
          <div
            ref={galleryRef}
            className="events-gallery"
            aria-label={copy.galleryLabel}
          >
            {eventImages.map((image) => (
              <a className="events-gallery-slide" href="/galleria" key={image.src}>
                <img
                  src={`${import.meta.env.BASE_URL}${image.src}`}
                  alt={language === "en" ? "Makai event space" : image.alt}
                  loading="lazy"
                  decoding="async"
                />
              </a>
            ))}
          </div>
          <div className="events-gallery-controls">
            <button type="button" aria-label={copy.previous} onClick={() => scrollGallery(-1)}>
              ←
            </button>
            <button type="button" aria-label={copy.next} onClick={() => scrollGallery(1)}>
              →
            </button>
            <a className="events-gallery-open" href="/galleria">
              {copy.openGallery}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
