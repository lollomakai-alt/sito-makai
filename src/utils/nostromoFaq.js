import { contactInfo } from "../data/contactInfo.js";

// Informazioni confermate dal gestore il 23 ottobre 2026.
const phone = contactInfo.phoneDisplay;
const dietarySafety = ` Le variazioni si concordano direttamente al telefono al ${phone} oppure al locale. La ciurma verifica ingredienti e preparazione: Nostromo non può confermare via chat l'assenza di allergeni o contaminazioni.`;

export function dietaryReply(text) {
  if (/\b(allerg\w*|sesamo|arachid\w*|frutta a guscio|nuts)\b/.test(text)) return null;
  const gluten = /\b(glutine|gluten|celiac\w*)\b/.test(text);
  const lactose = /\b(lattosio|lactose)\b/.test(text);
  if (gluten && lactose) return "Capitano, abbiamo farina e salsa di soia senza glutine e possiamo concordare variazioni per glutine e lattosio." + dietarySafety;
  if (gluten) return "Certo, Capitano! In cambusa abbiamo farina e salsa di soia senza glutine e possiamo concordare variazioni ai piatti. Se sei celiaco, avvisa la ciurma." + dietarySafety;
  if (lactose) return "Possiamo concordare variazioni ai piatti per il lattosio, Capitano! Segnala alla ciurma la tua esigenza." + dietarySafety;
  return null;
}

export function approvedVenueReply(text) {
  // Richieste operative restano nel percorso prenotazioni e gestione esistente.
  if (/\b(prenot\w*|disponibil\w*|conferm\w*|cancell\w*|annull\w*|modific\w*|riserv\w*)\b/.test(text)) return null;
  if (/\b(bambin\w*|bimb\w*|piccoli pirati|menu baby)\b/.test(text)) return "Per i piccoli pirati abbiamo piatti a tema One Piece da far brillare gli occhi: carne con osso per una fame da Luffy, udon e Cestino del Pirata! Quale tesoro vuole assaggiare il giovane della ciurma?";
  if (/\b(poco dolc\w*|meno dolc\w*|non (?:troppo )?dolc\w*)\b/.test(text)) return "Se il dolce non è la tua rotta, punta su Hurricane, Belladonna o Bourbon Special! Tre proposte da cui partire: chiedi al barman quale incontra meglio i tuoi gusti.";
  if (/\b(cane|cani|animali|quattro zampe)\b/.test(text)) return "Certo! Anche il tuo compagno a quattro zampe è il benvenuto a bordo del Makai. La ciurma si allarga!";
  if (/\b(all aperto|esterni|dehors|fuori)\b/.test(text)) return "Sì, Capitano! Abbiamo anche tavoli all’aperto per il tuo approdo. Per disponibilità e sistemazione, chiedi alla ciurma quando prenoti.";
  if (/\b(accessibil\w*|sedia a rotelle|sedie a rotelle|carrozzina|disabil\w*)\b/.test(text)) return "Sì, il Makai è accessibile in sedia a rotelle. Se hai esigenze specifiche per la sistemazione, comunicacele quando prenoti: prepariamo il tuo approdo.";
  if (/\b(privatizz\w*|esclusiva|tutto il locale)\b/.test(text)) return `Vuoi il Makai tutto per la tua ciurma? Chiama il ${phone} per valutare disponibilità, spazi e condizioni della privatizzazione.`;
  if (/\b(preventiv\w*)\b/.test(text)) return `Per organizzare il tuo banchetto, chiama la ciurma al ${phone}! Tieni pronti data, numero di invitati e tipo di festa: tracceremo insieme la rotta.`;
  if (/\b(fest\w*|compleann\w*|laure\w*|event\w*|pacchett\w*|apericena|aperitivo|menu per gruppi)\b/.test(text)) return `Compleanno, laurea o ciurma in festa? Puoi scegliere tra aperitivo, cena/apericena e dopocena. Per il dopocena trovi le formule Drink + torta, Drink + snack oppure Drink + prosecco. Chiama il ${phone} per organizzare la tua festa!`;
  if (/\b(dopocena|dopo cena)\b/.test(text)) return "Eccome, Capitano! Dalle 23:00 puoi salire a bordo anche solo per bere un cocktail. Se vuoi prenotare, scegli DOPOCENA su /prenota e attendi la conferma della ciurma.";
  return null;
}
