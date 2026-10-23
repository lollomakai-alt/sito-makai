import { menuPages } from "../data/siteContent.js";

export function normalize(text) {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[’']/g, " ");
}

// Correct only known navigation words; never guess a dish name or ingredient.
export function normalizeQuestion(text) {
  const corrections = { prenotrare: "prenotare", prenottare: "prenotare", prenottazione: "prenotazione", coctail: "cocktail", coktail: "cocktail", cocktai: "cocktail", analcolico: "analcolici", vegeteriano: "vegetariano", vegeteriani: "vegetariani" };
  return normalize(text).replace(/\b[a-z]+\b/g, word => corrections[word] ?? word).replace(/\s+/g, " ").trim();
}

const filler = new Set("mi me ti tu ci vi un uno una dei del della delle degli da di con col coi al alla ai alle nel nella nei nelle sul sulla sui sulle lo la le il gli i e o ma che cosa quale quali come per puoi posso potete avete vorrei voglio consigli consigliami consiglio suggerisci suggerimento qualcosa sapere vedere avere trovi trovo vostro vostri vostra vostre menu piatto piatti cibo food cocktail cocktails drink drinks mangiare bere cena pranzo quanto costa costano prezzo prezzi costi spesa euro sono anche invece altro altra altri altre meglio po grazie piacerebbe piace piacciono".split(" "));
for (const word of ["ingredienti", "ingrediente", "contiene", "contengono", "ha", "hanno", "composizione"]) filler.add(word);
for (const word of ["ciao", "salve", "ahoy", "buonasera", "buongiorno", "mostra", "mostrami", "vedere", "dammi", "lista", "elenco", "qualche", "proponi", "propormi", "cercare", "cerco", "cerca"]) filler.add(word);

export function menuSearchTerms(message) {
  return [...new Set(normalizeQuestion(message).match(/[a-z0-9]+/g) ?? [])]
    .filter(word => !filler.has(word) && !/^\d+$/.test(word));
}

export function publishedMenuReply(data, { topic = "menu", searchTerms = [], offset = 0 } = {}) {
  const menu = data?.menu ?? data;
  if (!menu || typeof menu !== "object" || Array.isArray(menu)) throw new Error("Invalid menu");
  const paths = topic === "drink" || topic === "analcolici" ? ["/menu-drink"] : topic === "food" ? ["/menu-food"] : ["/menu-food", "/menu-drink"];
  const categories = paths.flatMap(path => menuPages[path].categories.map(category => ({ ...category, path })));
  const selected = topic === "analcolici" ? categories.filter(category => category.menuKey === "analcolici") : categories;
  if (!selected.some(category => Array.isArray(menu[category.menuKey]))) throw new Error("Invalid menu categories");

  const items = selected.flatMap(category => (Array.isArray(menu[category.menuKey]) ? menu[category.menuKey] : [])
    .filter(item => item && typeof item.name_it === "string" && item.name_it.trim())
    .map(item => ({ ...item, path: category.path, searchable: normalize(`${item.name_it} ${item.description_it ?? ""} ${category.title}`) })));
  const matches = items.filter(item => searchTerms.every(term => item.searchable.split(/[^a-z0-9]+/).includes(term)));
  const links = paths.join(" e ");
  if (!matches.length) return `Non trovo voci corrispondenti nella descrizione pubblicata, Capitano. Consulta ${links} oppure chiedi alla ciurma per una scelta su misura. Non deduco ingredienti o caratteristiche che il menu non indica.`;
  if (offset >= matches.length) return `Hai visto tutte le voci corrispondenti nel menu pubblicato, Capitano. Per altre scelte consulta ${links} o dimmi un altro ingrediente.`;
  const lines = matches.slice(offset, offset + 3).map(item => {
    const price = (typeof item.price === "number" || typeof item.price === "string" && /^\d+(\.\d+)?$/.test(item.price)) ? Number(item.price) : NaN;
    const priceLabel = Number.isFinite(price) && price >= 0 ? ` — ${price.toLocaleString("it-IT", { style: "currency", currency: "EUR" })}` : "";
    const description = typeof item.description_it === "string" && item.description_it.trim() ? `\n${item.description_it.trim().slice(0, 240)}${item.description_it.trim().length > 240 ? "…" : ""}` : "";
    return `• ${item.name_it.trim()}${priceLabel}${description}`;
  });
  return `Dalle voci pubblicate del Makai, Capitano:\n\n${lines.join("\n\n")}\n\nMenu completo: ${links}. Sono informazioni del menu, non una verifica della disponibilità del giorno. Per allergie o ingredienti non indicati, chiedi alla ciurma.`;
}
