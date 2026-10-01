import { useEffect, useState } from "react";
import { galleryImages } from "../data/siteContent";
import { siteCopy } from "../i18n/copy";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function GalleryPage({ containerRef }) {
  const { language } = useLanguage();
  const copy = siteCopy[language];
  const [selectedImage, setSelectedImage] = useState(null);
  const imageAlt = (image) => language === "en" ? "Makai Grand Line venue, food and Tiki atmosphere" : image.alt;

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
        <a href="/" className="brand" aria-label={copy.common.brandHome}>
          <img
            src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.PNG`}
            alt="Makai Grand Line"
            className="logo-full"
          />
        </a>
        <div className="detail-header-actions">
          <a href="/" className="gallery-back-home">{copy.common.backShort}</a>
          <LanguageSwitcher className="detail-language" />
        </div>
      </header>

      <main className="gallery-page-main">
        <section className="gallery-page-section content-section">
          <h1 className="gallery-page-title">{copy.gallery.title}</h1>
          <div className="gallery-grid">
            {galleryImages.map((image, index) => (
              <button
                className="gallery-card"
                type="button"
                key={image.src}
                onClick={() => setSelectedImage(image)}
                aria-label={`${copy.gallery.openPhoto}: ${imageAlt(image)}`}
              >
                <img
                  src={`${import.meta.env.BASE_URL}${image.src}`}
                  alt={imageAlt(image)}
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
          aria-label={imageAlt(selectedImage)}
          onClick={() => setSelectedImage(null)}
        >
          <button
            className="gallery-lightbox-close"
            type="button"
            onClick={() => setSelectedImage(null)}
            aria-label={copy.gallery.closePhoto}
          >
            <span aria-hidden="true">×</span>
          </button>
          <img
            className="gallery-lightbox-image"
            src={`${import.meta.env.BASE_URL}${selectedImage.src}`}
            alt={imageAlt(selectedImage)}
            onClick={(event) => event.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
