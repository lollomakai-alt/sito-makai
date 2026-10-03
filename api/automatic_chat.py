import re
import unicodedata
from typing import Iterable, Optional

from config import (
    AFTER_DINNER_RESERVATION_END,
    AFTER_DINNER_RESERVATION_START,
    SLOT_END,
    SLOT_START,
    VENUE_CLOSE_TIME,
)
from menu_data import get_menu_data
from prenotazioni import _serializer, _reply, SESSION_SECONDS, PHONE
from itsdangerous import BadSignature
from chat_language import understand, intent, people_count, dietary_preferences
from chat_events import answer_event
from chat_menu import answer_menu


CONTACTS = {
    "address": "Via Braccio da Montone, 3/B, 00100 Roma RM",
    "phone": PHONE,
    "email": "makairoma@gmail.com",
}

OPENING_HOURS = (
    f"Lunedì chiuso. Da martedì a domenica il locale chiude alle {VENUE_CLOSE_TIME}. "
    f"Per la cena gli orari sono dalle {SLOT_START} alle {SLOT_END}. "
    f"Per prenotare il dopocena, disponibile dalle {AFTER_DINNER_RESERVATION_START} "
    f"alle {AFTER_DINNER_RESERVATION_END}, chiama il locale al {CONTACTS['phone']}. "
    "La cucina è aperta fino alle 23:30."
)

TRAVEL_INFO = (
    f"Il nostro approdo è in {CONTACTS['address']}. La Metro C è vicinissima al locale; "
    "nelle immediate vicinanze trovi anche parcheggi privati custoditi e parcheggi liberi. "
    f"Per maggiori indicazioni chiama la ciurma al {CONTACTS['phone']}."
)

LOCAL_INTRO = (
    "Il Makai Grand Line è un Tiki cocktail bar e ristorante al Pigneto, "
    "dove l'anima polinesiana incontra l'avventura piratesca ispirata a One Piece. "
    "A bordo trovi cocktail Tiki serviti in mug scenografici, cucina fusion, musica dal vivo "
    "e uno spazio per compleanni, lauree e feste. "
    f"Il nostro approdo è in {CONTACTS['address']}. Vuoi conoscere menu, cocktail, orari ed eventi?"
)

PIRATE_OPENERS = (
    "🏴‍☠️ Arrr, Capitano!",
    "🏴‍☠️ La ciurma risponde:",
    "🏴‍☠️ Rotta tracciata:",
    "🏴‍☠️ Dal diario di bordo:",
    "🏴‍☠️ Eccomi sul ponte:",
)


BOOKING_REDIRECT = (
    "La chat si occupa solo di informazioni e non registra prenotazioni. "
    "Trovi la pagina dedicata qui: /prenotazioni. "
    f"Al momento le prenotazioni online non sono ancora attive: per prenotare, modificare "
    f"o annullare un tavolo e verificare la disponibilità chiama il {PHONE}."
)


def _contextual_quick_replies(outgoing, context):
    if context.get("intent") == "event":
        event = context.get("event", {})
        if event.get("awaiting_bottles"):
            return ["1 bottiglia", "2 bottiglie", "3 bottiglie", "Niente prosecco"]
        if not event.get("category"):
            return ["Aperitivo", "Cena / apericena", "Dopocena"]
        if event.get("category") == "dopo cena" and not event.get("package"):
            return ["Drink + torta", "Drink + snack", "Drink + prosecco"]
        if event.get("category") and not event.get("people"):
            return ["10 persone", "15 persone", "20 persone", "30 persone"]
        return ["Quali sono i contatti?", "Consigliami un cocktail", "Nuovo evento"]

    if context.get("people") and not context.get("intent"):
        return ["Informazioni sul locale", "Informazioni per una festa"]
    return []

# Per le condizioni non documentate, il bot rimanda alla verifica con il locale.
FAQ = {
    ("parcheggio", "parcheggi", "parcheggiare"): f"Vicino al Makai trovi parcheggi privati custoditi e parcheggi liberi. Per maggiori informazioni chiama la ciurma al {CONTACTS['phone']}.",
    ("carta", "bancomat", "pagamenti"): "Accettiamo pagamenti con tutti i circuiti Bancomat.",
    ("animali", "cane", "cani"): f"Prima di salpare con il tuo compagno a quattro zampe, verifica con la ciurma al {CONTACTS['phone']}.",
    ("asporto", "delivery", "portare via", "consegna", "domicilio"): "Non facciamo asporto né consegna a domicilio.",
    ("prezzi", "quanto costa", "quanto si spende", "spesa media"): "La spesa media indicativa è di circa 30 € per una cena con drink.",
}

STOPWORDS = {
    "quali", "quale", "avete", "vorrei", "cosa", "come", "sono", "della", "delle",
    "questo", "questa", "cocktail", "drink", "menu", "piatti", "piatto", "cibo",
    "mangiare", "bere", "dolce", "dolci", "molto", "anche", "fatto", "fate",
}



def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9 ]+", " ", without_accents).strip()


def _pirate_reply(reply: str, opener_index: int = 0) -> str:
    """Mantiene chiare le informazioni e dà a ogni risposta la voce della ciurma."""
    if not reply or reply.startswith(("🏴‍☠️", "Alla prossima")):
        return reply
    opener = PIRATE_OPENERS[opener_index % len(PIRATE_OPENERS)]
    return f"{opener} {reply}"


def _contains_any(text: str, words: Iterable[str]) -> bool:
    """Parole corte (<=4 lettere): parola intera. Più lunghe: inizio di parola (allerg -> allergia)."""
    for word in words:
        w = re.escape(_normalize(word))
        pattern = rf"\b{w}\b" if len(word) <= 4 else rf"\b{w}"
        if re.search(pattern, text):
            return True
    return False


def _menu_items(menu_data, section_names: Iterable[str]):
    menu = menu_data["menu"]
    return [item for section in section_names for item in menu.get(section, [])]


def _format_menu(items, limit: int = 6) -> str:
    lines = [f"• {item['name_it']} — €{item['price']:.2f}" for item in items[:limit]]
    return "\n".join(lines)


def _find_matching_dishes(message: str, menu_data):
    words = {w for w in message.split() if len(w) >= 4 and w not in STOPWORDS}
    if not words:
        return []

    scored = []
    for item in _menu_items(menu_data, menu_data["menu"].keys()):
        name = _normalize(item["name_it"])
        desc = _normalize(item["description_it"])
        score = sum(2 for w in words if w in name) + sum(1 for w in words if w in desc)
        if score >= 2:
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored]


def _info(message_or_text: str, context=None):
    """Risposte informative a regole. Ritorna None se non capisce."""
    text = _normalize(message_or_text)

    asks_for_local_intro = text in ("info", "informazioni", "chi siete") or bool(re.search(
        r"\b(?:info|informazioni|parlami|raccontami)\b.*\b(?:locale|makai|voi)\b|"
        r"\b(?:cos e|che cos e)\s+(?:il\s+)?makai\b|\bchi siete\b",
        text,
    ))
    if asks_for_local_intro:
        return LOCAL_INTRO

    if len(text.split()) <= 3 and _contains_any(text, ("ciao", "salve", "buonasera", "buongiorno", "aloha")):
        return "Posso aiutarti con menu, cocktail, contatti, indicazioni ed eventi. Quale rotta scegli?"

    if _contains_any(text, ("come stai", "tutto bene", "come va")):
        return "Vento favorevole, vele spiegate e nessun ammutinamento all'orizzonte. E tu?"

    if _contains_any(text, ("grazie", "arrivederci", "a presto")):
        return "Alla prossima, pirata! Buon vento dalla ciurma del Makai."

    if _contains_any(text, ("indirizzo", "dove siete", "dove si trova", "come arrivo", "mappa", "metro", "mezzi", "trasporti")):
        return TRAVEL_INFO + " Nella sezione Contatti puoi aprire direttamente Google Maps."

    if _contains_any(text, ("telefono", "cellulare", "whatsapp", "chiamare", "contatto")):
        return f"Puoi chiamarci o scriverci su WhatsApp al {CONTACTS['phone']}."

    if _contains_any(text, ("email", "mail")):
        return f"La nostra email è {CONTACTS['email']}."

    if _contains_any(text, ("instagram", "facebook", "social")):
        return "Trovi la ciurma su Instagram come @makai_pigneto e su Facebook come Makai Surf And Tiki Bar."

    if "cucina" in text and _contains_any(
        text, ("orari", "orario", "apre", "aperta", "chiude", "fino", "quando")
    ):
        return "La cucina del Makai è aperta fino alle 23:30."

    if _contains_any(text, ("orari", "orario", "aprite", "aperti", "chiudete", "chiuso")):
        return OPENING_HOURS

    if _contains_any(text, ("evento", "eventi", "compleanno", "laurea", "festa", "feste")):
        return (
            "Al Makai puoi organizzare compleanni, lauree e feste in atmosfera Tiki e piratesca. "
            f"Per organizzare l'evento contattaci al {CONTACTS['phone']} o a {CONTACTS['email']}."
        )

    if _contains_any(text, ("allerg", "celiach", "glutine", "intoller", "vegetarian", "vegano")):
        return (
            "Per allergie o esigenze alimentari serve una verifica diretta con il locale: "
            f"contattaci al {CONTACTS['phone']} prima di ordinare."
        )

    for keys, answer in FAQ.items():
        if answer and _contains_any(text, keys):
            return answer

    menu_terms = (
        "menu", "mangiare", "cibo", "food", "piatti", "sushi", "burger",
        "udon", "cocktail", "drink", "bere", "rum", "tiki", "dolce",
        "dessert", "snack", "analcolico",
    )

    try:
        menu_data = get_menu_data()
    except Exception:
        if _contains_any(text, menu_terms):
            return (
                "Il menu è momentaneamente fuori rotta. Riprova tra poco oppure "
                f"contattaci al {CONTACTS['phone']}."
            )
        return None

    matches = _find_matching_dishes(text, menu_data)
    if matches or _contains_any(text, menu_terms):
        menu_context = context if context is not None else {}
        if matches and intent(text) is None:
            drinks = _menu_items(menu_data, ("cocktails", "analcolici", "volcanoes"))
            menu_context["menu_topic"] = "cocktail" if matches[0] in drinks else "menu"
        return answer_menu(text, menu_context, lambda: menu_data, PHONE)

    return None


def answer_message(message: str, session_id: str) -> str:
    """Compatibilità con vecchi caller: restituisce solo il testo della risposta."""
    result = answer_chat(message, session_id)
    return result["reply"] if isinstance(result, dict) else str(result)


def answer_chat(message: str, session_token: Optional[str]):
    """Sessione informativa: non avvia o riprende prenotazioni."""
    state = None
    if session_token:
        try:
            state = _serializer().loads(session_token, max_age=SESSION_SECONDS)
            if not isinstance(state, dict) or not isinstance(state.get("step"), str):
                raise BadSignature("Invalid chat state")
        except (BadSignature, RuntimeError):
            # Information requests can proceed with a fresh context after expiry.
            state = None
    # Retire old booking sessions before processing any confirmation or personal data.
    if state and state.get("step") != "assistente":
        return {"reply": _pirate_reply(BOOKING_REDIRECT), "session_token": None,
                "quick_replies": ["Informazioni sul locale", "Quali sono gli orari?"]}
    context = dict((state or {}).get("context", {}))
    context.pop("booking_draft", None)
    if context.get("intent") == "booking":
        context.pop("intent", None)
    text = understand(message)
    topic = intent(text)
    if topic is not None:
        context.pop("unrecognised_count", None)
    preferences = dietary_preferences(text)
    if preferences:
        context["preferences"] = sorted(set(context.get("preferences", []) + preferences))
    if re.search(r"non (?:sono|siamo) vegetarian|nessuna (?:preferenza|esigenza)", text):
        context["preferences"] = []
    count = people_count(text, bare=context.get("intent") == "event" and not context.get("event", {}).get("awaiting_bottles"))
    if count is not None:
        context["people"] = count

    def respond(reply):
        outgoing = {"step": "assistente"}
        quick_replies = _contextual_quick_replies(outgoing, context)
        reply_count = int(context.get("reply_count", 0))
        reply = _pirate_reply(reply, reply_count)
        context["reply_count"] = reply_count + 1
        outgoing["context"] = context
        try:
            response = _reply(reply, outgoing)
            if quick_replies is not None:
                response["quick_replies"] = quick_replies
            return response
        except RuntimeError:
            # Basic information remains usable if session configuration is missing.
            response = {"reply": reply, "session_token": None}
            if quick_replies is not None:
                response["quick_replies"] = quick_replies
            return response

    if re.fullmatch(r"(?:ricomincia|reset|annulla|basta|stop|cambiamo argomento|cambia argomento)[.!? ]*", text):
        context.clear()
        return respond("Va bene, cambiamo rotta. Vuoi informazioni su menu, cocktail, orari o eventi?")
    if topic in ("booking", "availability"):
        context.pop("intent", None)
        return respond(BOOKING_REDIRECT)
    if topic == "info":
        reply = _info(text)
        if reply:
            context["intent"] = "info"
            return respond(reply)
    # Un vecchio topic evento vale solo quando il messaggio corrente non esprime
    # già un nuovo intento. Così una richiesta esplicita di menu o drink cambia rotta,
    # ma un passaggio dell'evento (pacchetto o numero ospiti) resta nel flusso evento.
    event_context = context.get("event", {})
    continuing_event_package = (
        context.get("intent") == "event"
        and event_context.get("category") == "dopo cena"
        and re.fullmatch(r"(?:drink\s*\+\s*)?(?:torta|snack|prosecco)[.!? ]*", text)
    )
    event_continuation = (
        context.get("intent") == "event"
        and (continuing_event_package or (topic is None and count is not None))
    )
    if topic == "event" or event_continuation or continuing_event_package:
        context["intent"] = "event"
        if "people" in context and "people" not in context.setdefault("event", {}):
            context["event"]["people"] = context["people"]
        return respond(answer_event(text, context, PHONE))

    if topic in ("menu", "cocktail") or (topic is None and context.get("intent") in ("menu", "cocktail") and
            re.search(r"consigl|altro|alternativa|dolce|fruttato|tropicale|fresco|secco|forte|disponibili", text)):
        context["intent"] = topic or context["intent"]
        return respond(answer_menu(text, context, get_menu_data, PHONE))

    if count is not None:
        if count > 40:
            return respond(f"Per {count} persone la richiesta va valutata direttamente con il locale al {PHONE}. Per eventi oltre 40 persone serve una valutazione in struttura.")
        if count > 6:
            return respond(f"Per {count} persone contattaci direttamente al {PHONE}. Se si tratta di una festa posso spiegarti i pacchetti.")
        return respond(f"Siete in {count}: vuoi informazioni sul locale o sui pacchetti festa?")
    reply = _info(text, context)
    if reply:
        context["intent"] = "info"
        return respond(reply)
    # An unrecognised answer must not keep offering the previous flow's choices.
    context.pop("intent", None)
    context.pop("people", None)
    misses = context.get("unrecognised_count", 0) + 1
    context["unrecognised_count"] = misses
    if misses > 1:
        return respond(f"Non riesco a capire questa richiesta. Puoi scegliere una domanda suggerita qui sotto oppure contattare il locale al {PHONE}.")
    return respond("Non ho capito a quale informazione ti riferisci. Puoi chiedermi menu, cocktail, orari, indicazioni o eventi.")
