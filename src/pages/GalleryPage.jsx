import { useEffect, useState } from "react";
import { galleryImages } from "../data/siteContent";

export default function GalleryPage({ containerRef }) {
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    if (!selectedImage) return undefined;

    const closeOnEscape = (event) => {
      if (event.key === "Escape") setSelectedImage(null);
    };

    document.addEventListener("keydown", closeOnEscape);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      document.body.style.overflow = "";
    };
  }, [selectedImage]);

  return (
    <div ref={containerRef} className="scroll-container gallery-page">
      <header className="gallery-page-header">
        <a href="/" className="brand" aria-label="Torna alla homepage Makai">
          <img
            src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.PNG`}
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
              <button
                className="gallery-card"
                type="button"
                key={image.src}
                onClick={() => setSelectedImage(image)}
                aria-label={`Apri la foto: ${image.alt}`}
              >
                <img
                  src={`${import.meta.env.BASE_URL}${image.src}`}
                  alt={image.alt}
                  loading={index < 3 ? "eager" : "lazy"}
                  decoding="async"
                />
              </button>
            ))}
          </div>
        </section>
      </main>

      {selectedImage && (
        <div
          className="gallery-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={selectedImage.alt}
          onClick={() => setSelectedImage(null)}
        >
          <button
            className="gallery-lightbox-close"
            type="button"
            onClick={() => setSelectedImage(null)}
            aria-label="Chiudi immagine"
          >
            <span aria-hidden="true">×</span>
          </button>
          <img
            className="gallery-lightbox-image"
            src={`${import.meta.env.BASE_URL}${selectedImage.src}`}
            alt={selectedImage.alt}
            onClick={(event) => event.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
