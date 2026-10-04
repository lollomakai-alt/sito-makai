export const menuPages = {
  "/menu-drink": {
    type: "cocktail",
    title: "Menu Drink",
    panelTitle: "Cocktail Tiki",
    description:
      "Rum, frutta tropicale e spezie: i nostri cocktail Tiki vi accompagnano in un viaggio tra sapori esotici e spirito d’avventura.",
    image: "images/drinktop.webp",
    imageAlt: "Cocktail Tiki del Makai",
    categories: [
      {
        id: "cocktails",
        title: "Cocktails",
        menuKey: "cocktails",
        images: [
          { src: "images/drink.webp", alt: "Selezione Cocktail Tiki" },
          { src: "images/drink2.webp", alt: "Cocktail tropicali" },
          { src: "images/Drink 11.webp", alt: "Drink esotici" },
          { src: "images/Drink10.webp", alt: "Cocktail del Makai" },
        ],
        items: [],
      },
      {
        id: "analcolici",
        title: "Analcolici",
        menuKey: "analcolici",
        image: "images/Drink10.webp",
        imageAlt: "Drink tropicale del Makai",
        items: [],
      },
      {
        id: "volcanoes",
        title: "Volcanoes",
        menuKey: "volcanoes",
        image: "images/Tiki mug .webp",
        imageAlt: "Tiki mug del Makai con fiamme decorative",
        items: [],
      },
    ],
  },
  "/menu-food": {
    type: "food",
    title: "Menu Food",
    panelTitle: "One Piece Food",
    description:
      "Un menù che è un omaggio dichiarato all'universo di One Piece: piatti pensati per chi ama mangiare come Luffy (senza limiti) e con la cura di Sanji (in cucina). Dalle portate street-food ispirate alle isole della Grand Line a rivisitazioni più elaborate, ogni piatto porta il nome e lo spirito di un personaggio o di un'avventura della serie. Ingredienti freschi, presentazione curata e quel tocco di follia piratesca che rende ogni portata un piccolo easter egg per i fan — e un'ottima scoperta per chi il manga non lo conosce ancora.",
    image: "images/menutop.webp",
    imageAlt: "Piatti del menu Makai ispirato a One Piece",
    categories: [
      {
        id: "snack",
        title: "Snack",
        menuKey: "snack",
        image: "images/panino.webp",
        imageAlt: "Snack del menu Makai",
        items: [],
      },
      {
        id: "sushi",
        title: "Sushi",
        menuKey: "sushi",
        images: [
          { src: "images/sushi.webp", alt: "Sushi del menu Makai" },
          { src: "images/sushi2.webp", alt: "Selezione di sushi del Makai" },
        ],
        items: [],
      },
      {
        id: "primi",
        title: "Primi",
        menuKey: "primi_starters",
        image: "images/udon.webp",
        imageAlt: "Udon del menu Makai",
        items: [],
      },
      {
        id: "secondi",
        title: "Secondi",
        menuKey: "secondi_main",
        image: "images/carne-osso.webp",
        imageAlt: "Secondo piatto del menu Makai",
        items: [],
      },
      {
        id: "dolci",
        title: "Dolci",
        menuKey: "dolci",
        image: "images/dolce3.webp",
        imageAlt: "Dolce del menu Makai",
        items: [],
      },
    ],
  },
};

const menuPagesEn = {
  "/menu-drink": {
    type: "cocktail",
    title: "Drinks Menu",
    panelTitle: "Tiki Cocktails",
    description:
      "Rum, tropical fruit and spices: our Tiki cocktails take you on a journey through exotic flavours and a spirit of adventure.",
    image: "images/drinktop.webp",
    imageAlt: "Makai Tiki cocktail",
    categories: [
      {
        id: "cocktails",
        title: "Cocktails",
        menuKey: "cocktails",
        images: [
          { src: "images/drink.webp", alt: "Selection of Tiki cocktails" },
          { src: "images/drink2.webp", alt: "Tropical cocktails" },
          { src: "images/Drink 11.webp", alt: "Exotic drinks" },
          { src: "images/Drink10.webp", alt: "Makai cocktails" },
        ],
        items: [],
      },
      { id: "analcolici", title: "Non-Alcoholic", menuKey: "analcolici", image: "images/Drink10.webp", imageAlt: "Makai tropical drink", items: [] },
      { id: "volcanoes", title: "Volcanoes", menuKey: "volcanoes", image: "images/Tiki mug .webp", imageAlt: "Makai Tiki mug with decorative flames", items: [] },
    ],
  },
  "/menu-food": {
    type: "food",
    title: "Food Menu",
    panelTitle: "One Piece Food",
    description:
      "A menu that openly pays tribute to the One Piece universe: dishes for those who love to eat like Luffy, prepared with Sanji's care in the kitchen. From street food inspired by the islands of the Grand Line to more elaborate creations, every dish carries the name and spirit of a character or adventure from the series. Fresh ingredients, careful presentation and a touch of pirate madness make every course a small Easter egg for fans and a delicious discovery for newcomers.",
    image: "images/menutop.webp",
    imageAlt: "Makai dishes inspired by One Piece",
    categories: [
      { id: "snack", title: "Snacks", menuKey: "snack", image: "images/panino.webp", imageAlt: "Makai menu snacks", items: [] },
      { id: "sushi", title: "Sushi", menuKey: "sushi", images: [{ src: "images/sushi.webp", alt: "Makai sushi" }, { src: "images/sushi2.webp", alt: "Makai sushi selection" }], items: [] },
      { id: "primi", title: "First Courses", menuKey: "primi_starters", image: "images/udon.webp", imageAlt: "Udon from the Makai menu", items: [] },
      { id: "secondi", title: "Main Courses", menuKey: "secondi_main", image: "images/carne-osso.webp", imageAlt: "Main course from the Makai menu", items: [] },
      { id: "dolci", title: "Desserts", menuKey: "dolci", image: "images/dolce3.webp", imageAlt: "Dessert from the Makai menu", items: [] },
    ],
  },
};

export function getMenuPage(path, language = "it") {
  return (language === "en" ? menuPagesEn : menuPages)[path];
}

export const galleryImages = [
  { src: "images/panino.webp", alt: "Panino del menu Makai" },
  { src: "images/sushi.webp", alt: "Sushi del menu Makai" },
  { src: "images/sushi2.webp", alt: "Selezione di sushi del Makai" },
  { src: "images/udon.webp", alt: "Udon del menu Makai" },
  { src: "images/carne-osso.webp", alt: "Carne con osso del menu Makai" },
  { src: "images/dolce3.webp", alt: "Dolce del menu Makai" },
  { src: "images/Chi siamo 2 .webp", alt: "Dettaglio della sezione Chi siamo" },
  { src: "images/Drink 11.webp", alt: "Cocktail del Makai" },
  { src: "images/Drink10.webp", alt: "Cocktail del Makai" },
  { src: "images/MENU56.webp", alt: "Menu del Makai" },
  { src: "images/SALA.webp", alt: "Sala principale del Makai" },
  { src: "images/SALA7.webp", alt: "Atmosfera Tiki nella sala del Makai" },
  { src: "images/Tiki mug .webp", alt: "Tiki mug del Makai" },
  { src: "images/Tramonto.webp", alt: "Tramonto sul mare" },
  { src: "images/Udon di oden .webp", alt: "Udon di oden" },
  { src: "images/chi-siamo.webp", alt: "Atmosfera e dettagli del Makai" },
  { src: "images/dolci.webp", alt: "Dolce del menu Makai" },
  { src: "images/drink.webp", alt: "Cocktail del Makai" },
  { src: "images/drink2.webp", alt: "Cocktail del Makai" },
  { src: "images/drinktop.webp", alt: "Cocktail Tiki del Makai" },
  { src: "images/eventi.webp", alt: "Evento al Makai" },
  { src: "images/foto-menu2.webp", alt: "Piatto del menu Makai" },
  { src: "images/makai inizio.webp", alt: "Interno del Makai" },
  { src: "images/menu.webp", alt: "Proposta gastronomica del Makai" },
  { src: "images/menutop.webp", alt: "Piatto del menu Makai" },
  { src: "images/foto-menu2-converted.webp", alt: "Dettagli del menu Makai" },
  { src: "images/sala12.webp", alt: "Sala del Makai" },
  { src: "images/sala5.webp", alt: "Spazi interni del Makai" },
  { src: "images/sala5-converted.webp", alt: "Dettagli della sala del Makai" },
  { src: "images/statua 3.webp", alt: "Statua decorativa del Makai" },
  { src: "images/statua.webp", alt: "Statua decorativa del Makai" },
  { src: "images/statua2.webp", alt: "Statua decorativa del Makai" },
  { src: "images/statua4.webp", alt: "Statua decorativa del Makai" },
  { src: "images/totem.webp", alt: "Totem e arredi Tiki del Makai" },
];
