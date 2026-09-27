export default function HomeMenuSection() {
  return (
    <section id="menu" className="menu-section content-section" aria-labelledby="menu-title">
      <h2 id="menu-title" className="menu-title">Menu</h2>
      <div className="menu-panels">
        <a className="menu-panel" href="/menu-drink">
          <div className="menu-panel-copy">
            <h3>Cocktail Tiki</h3>
            <p>
              Rum, frutta tropicale e spezie: i nostri cocktail Tiki vi
              accompagnano in un viaggio tra sapori esotici e spirito d’avventura.
            </p>
          </div>
          <img
            src={`${import.meta.env.BASE_URL}images/drinktop.jpeg`}
            alt="Cocktail Tiki del Makai"
            width="1179"
            height="1592"
            loading="lazy"
            decoding="async"
          />
        </a>

        <a className="menu-panel" href="/menu-food">
          <div className="menu-panel-copy">
            <h3>One Piece Food</h3>
            <p>
              Salpate sulla Grand Line con un menù ispirato a One Piece: dai
              piatti amati da Luffy alle ricette di Sanji, ogni boccone è
              un’avventura da condividere con la vostra ciurma.
            </p>
          </div>
          <img
            src={`${import.meta.env.BASE_URL}images/menutop.jpeg`}
            alt="Piatti del menu Makai ispirato a One Piece"
            width="1179"
            height="1561"
            loading="lazy"
            decoding="async"
          />
        </a>
      </div>
    </section>
  );
}
