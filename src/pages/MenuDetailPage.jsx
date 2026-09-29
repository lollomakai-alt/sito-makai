import { useEffect, useState } from "react";

function formatPrice(price) {
  return Number(price).toLocaleString("it-IT", {
    style: "currency",
    currency: "EUR",
  });
}

export default function MenuDetailPage({ containerRef, page }) {
  // Riconosce se la pagina richiede dati dinamici (food o cocktail)
  const isDynamicMenu = page.type === "food" || page.type === "cocktail";
  
  const [menu, setMenu] = useState(null);
  const [menuStatus, setMenuStatus] = useState(isDynamicMenu ? "loading" : "idle");

  useEffect(() => {
    if (!isDynamicMenu) return undefined;

    const controller = new AbortController();
    setMenuStatus("loading");

    // Se un domani avrai un endpoint separato (es. /api/cocktails), puoi gestirlo qui. 
    // Per ora usa /api/menu che restituisce tutto il catalogo.
    fetch("/api/menu", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Menu API: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        // Se il backend restituisce un oggetto unico, adattalo qui (es. data.menu o data.cocktails)
        setMenu(data.menu || data);
        setMenuStatus("ready");
      })
      .catch((error) => {
        if (error.name !== "AbortError") setMenuStatus("error");
      });

    return () => controller.abort();
  }, [isDynamicMenu]);

  const categories = page.categories
    ? page.categories.map((category) => ({
        ...category,
        items: menu?.[category.menuKey] ?? [],
      }))
    : [];

  return (
    <div ref={containerRef} className="scroll-container menu-detail-page">
      <header className="menu-detail-header">
        <a href="/" className="brand" aria-label="Torna alla homepage Makai">
          <img
            src={`${import.meta.env.BASE_URL}images/logo/Makai-grandline.PNG`}
            alt="Makai Grand Line"
            className="logo-full"
          />
        </a>
        <a href="/" className="back-home-link">← Torna alla homepage</a>
      </header>

      <main className="menu-detail-main">
        <section className={`menu-detail-section content-section${isDynamicMenu ? " menu-food-detail-section" : ""}`}>
          <h1 className="menu-detail-title">{page.title}</h1>
          
          {/* Pannello principale di presentazione della categoria */}
          <article className="menu-detail-panel">
            {page.image && (
              <img
                src={`${import.meta.env.BASE_URL}${page.image}`}
                alt={page.imageAlt || page.title}
              />
            )}
            <div className="menu-detail-copy">
              <h2>{page.panelTitle}</h2>
              <p>{page.description}</p>
            </div>
          </article>

          {/* Sezione categorie dinamiche (funziona identica per food e cocktail) */}
          {isDynamicMenu && (
            <div className="menu-food-categories" aria-label="Categorie del menu">
              {menuStatus === "loading" && (
                <p className="menu-food-status" role="status">Caricamento del menu…</p>
              )}
              {menuStatus === "error" && (
                <p className="menu-food-status menu-food-error" role="alert">
                  Il menu è momentaneamente fuori rotta. Riprova tra poco.
                </p>
              )}
              
              {menuStatus === "ready" && categories.map((category, index) => (
                <article
                  className={`menu-food-category-panel${index % 2 === 1 ? " is-reversed" : ""}`}
                  key={category.id}
                >
                  <div className="menu-food-category-copy">
                    <h2>{category.title}</h2>
                    <div className="menu-food-items">
                      {category.items && category.items.length > 0 ? (
                        category.items.map((item) => (
                          <article className="menu-food-item" key={item.id}>
                            <div className="menu-food-item-heading">
                              <h3>{item.name_it}</h3>
                              <span>{formatPrice(item.price)}</span>
                            </div>
                            {item.description_it && <p>{item.description_it}</p>}
                          </article>
                        ))
                      ) : (
                        <p className="menu-empty-category">Nessun elemento disponibile in questa categoria.</p>
                      )}
                    </div>
                  </div>
                  
                  {/* Immagini categoria: supporta sia singola (image) che multiple (images[]) */}
                  {(category.image || (category.images && category.images.length > 0)) && (
                    <div className="menu-food-category-media">
                      {category.images && category.images.length > 0 ? (
                        <div className="cocktail-carousel">
                          {category.images.map((img, i) => (
                            <img
                              key={i}
                              src={`${import.meta.env.BASE_URL}${img.src}`}
                              alt={img.alt || category.title}
                              loading="lazy"
                              decoding="async"
                            />
                          ))}
                        </div>
                      ) : (
                        <img
                          src={`${import.meta.env.BASE_URL}${category.image}`}
                          alt={category.imageAlt || category.title}
                          loading="lazy"
                          decoding="async"
                        />
                      )}
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}