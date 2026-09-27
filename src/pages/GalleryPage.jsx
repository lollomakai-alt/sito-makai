import { galleryImages } from "../data/siteContent";

export default function GalleryPage({ containerRef }) {
  return (
    <div ref={containerRef} className="scroll-container gallery-page">
      <header className="gallery-page-header">
        <a href="/" className="brand" aria-label="Torna alla homepage Makai">
          <img
            src={`${import.meta.env.BASE_URL}images/Makai-grandline.PNG`}
            alt="Makai Grand Line"
            className="logo-full"
          />
        </a>
        <a href="/" className="gallery-back-home">← Torna alla homepage</a>
      </header>

      <main className="gallery-page-main">
        <section className="gallery-page-section content-section">
          <h1 className="gallery-page-title">Galleria</h1>
          <div className="gallery-grid">
            {galleryImages.map((image, index) => (
              <figure className="gallery-card" key={image.src}>
                <img
                  src={`${import.meta.env.BASE_URL}${image.src}`}
                  alt={image.alt}
                  loading={index < 3 ? "eager" : "lazy"}
                  decoding="async"
                />
              </figure>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
