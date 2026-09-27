export default function MenuDetailPage({ containerRef, page }) {
  return (
    <div ref={containerRef} className="scroll-container menu-detail-page">
      <header className="menu-detail-header">
        <a href="/" className="brand" aria-label="Torna alla homepage Makai">
          <img
            src={`${import.meta.env.BASE_URL}images/Makai-grandline.PNG`}
            alt="Makai Grand Line"
            className="logo-full"
          />
        </a>
        <a href="/" className="back-home-link">← Torna alla homepage</a>
      </header>

      <main className="menu-detail-main">
        <section className="menu-detail-section content-section">
          <h1 className="menu-detail-title">{page.title}</h1>
          <article className="menu-detail-panel">
            <img
              src={`${import.meta.env.BASE_URL}${page.image}`}
              alt={page.imageAlt}
            />
            <div className="menu-detail-copy">
              <h2>{page.panelTitle}</h2>
              <p>{page.description}</p>
              <p className="menu-backend-note">
                La carta completa sarà disponibile qui.
              </p>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
