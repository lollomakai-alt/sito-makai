import { useEffect, useRef, useState } from "react";
import { eventImages } from "virtual:event-images";
import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";
import HomeSectionHeading from "./HomeSectionHeading";

export default function EventsSection() {
  const { language } = useLanguage();
  const copy = siteCopy[language].events;
  const sectionRef = useRef(null);
  const galleryRef = useRef(null);
  const loadedCountRef = useRef(2);
  const [loadedCount, setLoadedCount] = useState(2);
  const [isNearViewport, setIsNearViewport] = useState(false);
  const [isGalleryPaused, setIsGalleryPaused] = useState(false);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section || !("IntersectionObserver" in window)) {
      setIsNearViewport(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsNearViewport(true);
          setLoadedCount((count) => Math.max(count, 4));
          observer.disconnect();
        }
      },
      { rootMargin: "600px 0px" },
    );
    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    loadedCountRef.current = loadedCount;
  }, [loadedCount]);

  const advanceGallery = (direction) => {
    const gallery = galleryRef.current;
    if (!gallery || !gallery.clientWidth || !gallery.children.length) return;
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";

    const currentIndex = Math.round(gallery.scrollLeft / gallery.clientWidth);
    const nextIndex = (currentIndex + direction + eventImages.length) % eventImages.length;
    if (nextIndex >= loadedCountRef.current) {
      loadedCountRef.current = Math.min(nextIndex + 1, eventImages.length);
      setLoadedCount(loadedCountRef.current);
      requestAnimationFrame(() => {
        gallery.scrollTo({ left: nextIndex * gallery.clientWidth, behavior });
      });
      return;
    }
    gallery.scrollTo({ left: nextIndex * gallery.clientWidth, behavior });
  };

  useEffect(() => {
    if (isGalleryPaused || !isNearViewport) return undefined;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let intervalId;
    const updateAutoplay = () => {
      window.clearInterval(intervalId);
      if (reducedMotion.matches) return;
      intervalId = window.setInterval(() => {
        advanceGallery(1);
      }, 3500);
    };
    updateAutoplay();
    reducedMotion.addEventListener("change", updateAutoplay);
    return () => {
      window.clearInterval(intervalId);
      reducedMotion.removeEventListener("change", updateAutoplay);
    };
  }, [isGalleryPaused, isNearViewport]);

  const scrollGallery = (direction) => {
    if (!isNearViewport) setIsNearViewport(true);
    advanceGallery(direction);
  };

  return (
    <section ref={sectionRef} id="eventi" className="events-section content-section" aria-labelledby="events-title">
      <HomeSectionHeading id="events-title" className="events-title">{copy.title}</HomeSectionHeading>
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
            {eventImages.slice(0, loadedCount).map((image) => (
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
