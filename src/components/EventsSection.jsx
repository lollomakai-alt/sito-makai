import { useEffect, useRef, useState } from "react";
import { eventImages } from "virtual:event-images";

export default function EventsSection() {
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
      <h2 id="events-title" className="events-title">Eventi</h2>
      <div className="events-layout">
        <div className="events-copy">
          <p>
            La vostra festa merita una rotta speciale. Radunate la ciurma e
            salpate verso Makai: tra cocktail Tiki, sapori ispirati alla Grand
            Line e atmosfere piratesche, sarete i protagonisti dell’avventura.
            Che sia un compleanno, una laurea o un traguardo da celebrare,
            lasciate la quotidianità a terra e immergetevi in un’esperienza da
            vivere con chi conta davvero. Al prossimo brindisi, il tesoro saranno
            i ricordi che porterete a casa.
          </p>
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
            aria-label="Galleria fotografica della sala eventi"
          >
            {eventImages.map((image) => (
              <a className="events-gallery-slide" href="/galleria" key={image.src}>
                <img
                  src={`${import.meta.env.BASE_URL}${image.src}`}
                  alt={image.alt}
                  loading="lazy"
                  decoding="async"
                />
              </a>
            ))}
          </div>
          <div className="events-gallery-controls">
            <button type="button" aria-label="Foto precedente" onClick={() => scrollGallery(-1)}>
              ←
            </button>
            <button type="button" aria-label="Foto successiva" onClick={() => scrollGallery(1)}>
              →
            </button>
            <a className="events-gallery-open" href="/galleria">
              Apri la galleria completa
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
