import { useRef } from "react";

const eventImages = [
  { src: "images/SALA.PNG", alt: "Sala del Makai allestita per gli eventi" },
  { src: "images/SALA7.PNG", alt: "Atmosfera della sala del Makai" },
  { src: "images/sala.JPG", alt: "Dettagli pirateschi della sala del Makai" },
  { src: "images/sala2.png", alt: "Spazi interni del Makai" },
];

export default function EventsSection() {
  const galleryRef = useRef(null);

  const scrollGallery = (direction) => {
    const gallery = galleryRef.current;
    if (!gallery) return;

    gallery.scrollBy({
      left: direction * gallery.clientWidth,
      behavior: "smooth",
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

        <div className="events-gallery-panel">
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
