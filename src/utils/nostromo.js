import { contactInfo } from "../data/contactInfo.js";
import { menuSearchTerms, normalize, normalizeQuestion, publishedMenuReply } from "./nostromoMenu.js";

export const BOOKING_PATH = "/prenota";
export const CHAT_TIMEOUT_MS = 15000;
export const quickQuestions = ["Menu da mangiare", "Menu da bere", "Dove siete?"];
export const welcomeMessage = "Ahoy! Sono Nostromo, la guida del Makai. Posso cercare piatti e cocktail nei menu pubblicati o aiutarti con il locale. Per prenotare, la rotta è /prenota.";
const bookingReply = "Ahoy! Per prenotare e consultare la disponibilità, apri /prenota. Qui in chat non verifico posti e non confermo prenotazioni. Per una prenotazione esistente usa il link ricevuto via email o chiama la ciurma al " + contactInfo.phoneDisplay + ".";
const allergyReply = "Per allergie, intolleranze o ingredienti da escludere, le eventuali variazioni si concordano direttamente al telefono al " + contactInfo.phoneDisplay + " oppure al locale. La ciurma verifica ingredienti e preparazione: Nostromo non può confermare via chat l'assenza di allergeni o contaminazioni.";
const vegetarianReply = "Per esigenze vegetariane possiamo concordare variazioni al menu direttamente al telefono al " + contactInfo.phoneDisplay + " oppure al locale. Chiedi alla ciurma quali piatti si possono adattare.";
const menuReply = "Per informazioni verificate su piatti e prezzi, consulta /menu-food; per i cocktail apri /menu-drink. Posso cercare una voce nel menu pubblicato: dimmi il nome o un ingrediente. Per dettagli non indicati chiama la ciurma al " + contactInfo.phoneDisplay + ".";
const contactsReply = `Il Makai è in ${contactInfo.address}, Capitano. Per chiamare la ciurma: ${contactInfo.phoneDisplay}. Trovi il collegamento alla mappa e gli altri recapiti in /#contatti.`;
const menuTopics = new Set(["menu", "food", "drink", "analcolici"]);

export function suggestionsFor(topic) {
  if (topic === "booking") return ["Dove siete?", "Orari di apertura?"];
  if (["allergy", "vegetarian", "vegan"].includes(topic)) return ["Come vi contatto?", "Menu da mangiare"];
  if (topic === "food") return ["E altri?", "Quali dolci avete?", "E i prezzi?"];
  if (["drink", "analcolici"].includes(topic)) return ["E altri?", "E gli analcolici?", "E i prezzi?"];
  return quickQuestions;
}

export function classifyQuestion(message, context = {}) {
  const text = normalizeQuestion(message);
  if (/^(?:(?:ciao|salve|ahoy|ehi|buongiorno|buonasera|hello|hi)[ ,.!?]*)+$/.test(text)) return { topic: "greeting" };
  if (/^(?:grazie(?: mille)?|perfetto|ok(?:ay)?|thanks|thank you)[.!?]*$/.test(text)) return { topic: "thanks" };
  if (/^(?:aiuto|help|non ho capito|non capisco|cosa (?:sai|puoi) fare|mi aiuti|cosa mi consigli)[.!?]*$/.test(text)) return { topic: "clarify" };
  if (/\b(allerg\w*|intolleran\w*|celiac\w*|glutine|gluten|contaminaz\w*|lattosio|lactose|nuts)\b|\b(senza|without)\s+(?!prenot|book|reserv|alcol|alcool|alcohol)\w+/.test(text)) return { topic: "allergy" };
  if (/\bvegetari\w*\b/.test(text)) return { topic: "vegetarian" };
  if (/\bvegan\w*\b/.test(text)) return { topic: "vegan" };
  const bookingText = text.replace(/\bnon (?:voglio|devo|intendo) prenotare\b/g, "");
  const explicitBooking = /\b(prenot\w*|disponibil\w*|conferm\w*|riconferm\w*|cancell\w*|annull\w*|tavol\w*|posti|posto|riserv\w*|book\w*|reserv\w*|availability|available|confirm\w*|cancel\w*|table|seats?)\b/.test(bookingText);
  // An explicit question about opening hours wins over isolated times/numbers.
  if (!explicitBooking && /\b(orari|aprite|apertura|chiudete|chiusura|apert[ioae]|opening|hours)\b/.test(text)) return { topic: "chat" };
  if (explicitBooking
      || /\b(siamo|saremo)(?:\s+in)?\s+(\d+|due|tre|quattro|cinque|sei|sette|otto|nove|dieci)\b|\b(per|for|party of)\s+\d+\b|\b(?:avete|hai|siete).{0,15}liber[ioae]\b/.test(bookingText)
      || context.topic === "booking" && /^(?:e |alle |per )?(?:oggi|domani|stasera|sabato|domenica|\d+(?:[:.]\d{2})?)[.!?]?$/.test(text)) return { topic: "booking" };
  if (/\b(dove (?:siete|vi trovate)|indirizzo|come (?:vi raggiungo|arrivo da voi|vi contatto)|contatt\w*|chiama\w*|numero|telefono|recapiti|address|mappa)\b/.test(text)) return { topic: "contact" };
  if (/^(?:\d+(?:[:.]\d{2})?|oggi|domani|stasera|dopodomani|today|tomorrow|tonight)[.!?]?$/.test(text)) return { topic: "clarify" };

  const alcoholFree = /\banalcolic\w*\b|\b(?:senza|without)\s+(?:alcol|alcool|alcohol)\b/.test(text);
  const drinks = alcoholFree || /\b(cocktail\w*|drink\w*|rum|bere|bevande)\b/.test(text);
  const food = /\b(piatt\w*|mang\w*|cibo|carne|pesce|pollo|sushi|dolc\w*|food|eat|dish\w*|cena)\b/.test(text);
  const menu = /€|\b(menu|prezz\w*|cost\w*|spend\w*|ingredient\w*|euro|price\w*)\b/.test(text);
  const followup = menuTopics.has(context.topic) && (/^(e |invece|altro|altr[aoie]\b|ancora|quanto)/.test(text) || /^(?:con |al |alla |col )\w+[.!?]?$/.test(text));
  if (drinks || food || menu || followup) {
    const topic = alcoholFree ? "analcolici" : drinks ? "drink" : food ? "food" : menuTopics.has(context.topic) ? context.topic : "menu";
    const terms = menuSearchTerms(message).filter(term => !/^analcolic/.test(term) && !(alcoholFree && /^(senza|without|alcol|alcool|alcohol)$/.test(term)));
    const more = /^(?:e )?(?:altro|altr[aoie]|ancora)(?:\?|\.)?$/.test(text);
    const searchTerms = more || !terms.length && menuTopics.has(context.topic) && !drinks && !food ? context.searchTerms ?? [] : terms;
    if (topic === "menu" && !searchTerms.length) return { topic: "menu-choice" };
    return { topic, searchTerms, offset: more ? (context.offset ?? 0) + 3 : 0 };
  }
  return { topic: "chat" };
}

function immediateReply(topic) {
  if (topic === "greeting") return welcomeMessage;
  if (topic === "thanks") return "Ai tuoi ordini, Capitano! Se ti serve altro, scegli una rotta qui sotto.";
  if (topic === "booking") return bookingReply;
  if (topic === "allergy") return allergyReply;
  if (topic === "vegetarian") return vegetarianReply;
  if (topic === "vegan") return `Per esigenze vegane, chiedi direttamente alla ciurma al ${contactInfo.phoneDisplay} oppure al locale quali opzioni o variazioni sono possibili. Non deduco questa caratteristica dagli ingredienti descritti nel menu.`;
  if (topic === "contact") return contactsReply;
  if (topic === "menu-choice") return "Quale rotta scegli, Capitano: menu da mangiare o da bere? Puoi aprire /menu-food e /menu-drink oppure indicarmi un piatto, un cocktail o un ingrediente da cercare.";
  if (topic === "clarify") return "Mi dai un dettaglio in più, Capitano? Vuoi sapere un orario, cercare nel menu o prenotare? Per prenotare apri /prenota.";
  return null;
}

export function localReply(message, context = {}) {
  return immediateReply(classifyQuestion(message, context).topic);
}

// Response safety rules are separate from question intent: an opening time is
// information, not a booking request. Only transactional booking claims redirect.
function guideResponse(reply) {
  const text = normalize(reply);
  if (/\b(prenotazion\w*|booking|reservation)\b.{0,40}\b(confermat\w*|registrat\w*|confirmed|complet\w*)\b|\b(tavol\w*|posti|seats?|table)\b.{0,30}\b(disponibil\w*|liber\w*|available)\b|\b(ho prenotato|dimmi il nome|lascia il telefono)\b/.test(text)) return bookingReply;
  if (/\b(allerg\w*|intolleran\w*|celiac\w*|glutine|gluten|lattosio|lactose|contaminaz\w*)\b/.test(text)) return allergyReply;
  if (/\bvegetari\w*\b/.test(text)) return vegetarianReply;
  if (/\bvegan\w*\b/.test(text)) return immediateReply("vegan");
  if (/€|\b(euro|cost[ao]|prezz\w*|ingredient\w*|piatt\w*|cocktail\w*|sushi|rum)\b/.test(text)) return menuReply;
  return null;
}

export class ChatError extends Error {
  constructor(code, retryAfter = 0, scope = "chat") { super(code); this.code = code; this.retryAfter = retryAfter; this.scope = scope; }
}

export function errorMessage(error) {
  const contact = ` Puoi riprovare o chiamare la ciurma al ${contactInfo.phoneDisplay}.`;
  if (error.code === "rate-limit") return `Un momento, Capitano: sono arrivate molte richieste. Attendi${error.retryAfter ? ` almeno ${error.retryAfter} secondi` : " un poco"} prima di riprovare.`;
  if (error.code === "menu-unavailable") return "Non riesco a leggere il menu aggiornato, Capitano. Puoi riprovare oppure aprire /menu-food o /menu-drink. Per dettagli chiama la ciurma al " + contactInfo.phoneDisplay + ".";
  if (error.code === "timeout") return "La risposta sta tardando, Capitano. Il collegamento è scaduto." + contact;
  if (error.code === "invalid-input") return "Scrivi una domanda da 1 a 500 caratteri, Capitano.";
  return "Rotta momentaneamente interrotta, Capitano: non ho ricevuto una risposta valida." + contact;
}

export async function requestReply(message, { sessionToken = null, context = {}, signal, fetchImpl = fetch, timeoutMs = CHAT_TIMEOUT_MS } = {}) {
  const text = message.trim();
  if (!text || text.length > 500) throw new ChatError("invalid-input");
  if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
  const intent = classifyQuestion(text, context);
  const reply = immediateReply(intent.topic);
  if (reply) return { reply, quickReplies: suggestionsFor(intent.topic), sessionToken: null, context: intent };

  const isMenu = menuTopics.has(intent.topic);
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetchImpl(isMenu ? "/api/menu" : "/api/chat", {
      method: isMenu ? "GET" : "POST", signal: controller.signal, cache: "no-store",
      ...(isMenu ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text, session_token: sessionToken }) }),
    });
    if (response.status === 429) {
      const value = response.headers.get("retry-after");
      const seconds = /^\d+$/.test(value ?? "") ? Number(value) : Math.ceil((Date.parse(value) - Date.now()) / 1000);
      throw new ChatError("rate-limit", Number.isFinite(seconds) ? Math.max(0, seconds) : 0, isMenu ? "menu" : "chat");
    }
    if (!response.ok) throw new ChatError(isMenu ? "menu-unavailable" : "unavailable");
    const data = await response.json();
    if (isMenu) return {
      reply: publishedMenuReply(data, intent),
      quickReplies: suggestionsFor(intent.topic),
      sessionToken: null, context: intent,
    };
    if (typeof data?.reply !== "string" || !data.reply.trim() || data.reply.length > 8000) throw new ChatError("invalid-response");
    const guidedReply = guideResponse(data.reply);
    return {
      reply: guidedReply || data.reply.trim().replace(/\/prenotazioni(?![\w/-])/g, BOOKING_PATH),
      quickReplies: guidedReply ? quickQuestions : Array.isArray(data.quick_replies) ? [...new Set(data.quick_replies.filter(item => typeof item === "string" && item.trim() && item.length <= 120).map(item => item.trim()))].slice(0, 4) : [],
      sessionToken: !guidedReply && typeof data.session_token === "string" ? data.session_token : null,
      context: { topic: "chat" },
    };
  } catch (error) {
    if (timedOut) throw new ChatError("timeout");
    if (controller.signal.aborted) throw error;
    if (error instanceof ChatError) throw error;
    throw new ChatError(isMenu ? "menu-unavailable" : "unavailable");
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abort);
  }
}
