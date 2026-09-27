import re
import unicodedata
from typing import Iterable

from menu_data import MAKAI_DATA


CONTACTS = {
    "address": "Via Braccio da Montone, 3/B, 00100 Roma RM",
    "phone": "339 751 4140",
    "email": "makairoma@gmail.com",
}

OPENING_HOURS = (
    "Lunedì chiuso. Da martedì a venerdì e domenica siamo aperti "
    "dalle 18:00 alle 01:00; sabato dalle 18:00 alle 02:00. "
    "La cucina è aperta fino alle 23:30."
)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9 ]+", " ", without_accents).strip()


def _contains_any(text: str, words: Iterable[str]) -> bool:
    return any(word in text for word in words)


def _menu_items(section_names: Iterable[str]):
    menu = MAKAI_DATA["menu"]
    return [item for section in section_names for item in menu.get(section, [])]


def _format_menu(items, limit: int = 6) -> str:
    lines = [f"• {item['name_it']} — €{item['price']:.2f}" for item in items[:limit]]
    return "\n".join(lines)


def _find_matching_dishes(message: str):
    words = {word for word in message.split() if len(word) >= 4}
    if not words:
        return []

    matches = []
    for item in _menu_items(MAKAI_DATA["menu"].keys()):
        searchable = _normalize(
            f"{item['name_it']} {item['description_it']} {item['category']}"
        )
        if any(word in searchable for word in words):
            matches.append(item)
    return matches


def answer_message(message: str) -> str:
    """Restituisce una risposta automatica usando soltanto i dati ufficiali Makai."""
    text = _normalize(message)

    if _contains_any(text, ("ciao", "salve", "buonasera", "buongiorno", "aloha")):
        return "Aloha, pirata! Posso aiutarti con menu, cocktail, contatti, indicazioni ed eventi del Makai."

    if _contains_any(text, ("indirizzo", "dove siete", "dove si trova", "come arrivo", "mappa")):
        return f"Ci trovi in {CONTACTS['address']}. Nella sezione Contatti puoi aprire direttamente Google Maps."

    if _contains_any(text, ("telefono", "numero", "whatsapp", "chiamare", "contatto")):
        return f"Puoi chiamarci o scriverci su WhatsApp al {CONTACTS['phone']}."

    if _contains_any(text, ("email", "mail")):
        return f"La nostra email è {CONTACTS['email']}."

    if "cucina" in text and _contains_any(
        text, ("orari", "orario", "apre", "aperta", "chiude", "fino", "quando")
    ):
        return "La cucina del Makai è aperta fino alle 23:30."

    if _contains_any(text, ("orari", "orario", "aprite", "aperti", "chiudete", "chiuso")):
        return OPENING_HOURS

    if _contains_any(text, ("prenota", "prenotare", "prenotazione", "tavolo", "posto")):
        return (
            "Per prenotare scrivici su WhatsApp al 339 751 4140 indicando nome, "
            "giorno, orario e numero di persone. La ciurma del Makai ti confermerà la disponibilità."
        )

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

    matches = _find_matching_dishes(text)
    if matches:
        details = [
            f"• {item['name_it']}: {item['description_it']} — €{item['price']:.2f}"
            for item in matches[:3]
        ]
        return "Ho trovato questi tesori nel menu:\n" + "\n".join(details)

    if _contains_any(text, ("cocktail", "drink", "bere", "rum", "tiki")):
        cocktails = _menu_items(("cocktails",))
        return "Ecco alcuni tesori della carta cocktail:\n" + _format_menu(cocktails)

    if _contains_any(text, ("menu", "mangiare", "cibo", "food", "piatti", "sushi", "burger", "udon")):
        food = _menu_items(("sushi", "primi_starters", "secondi_main"))
        return (
            "La cucina segue la Rotta Maggiore con sushi e piatti ispirati a One Piece. "
            "Ecco alcune proposte:\n" + _format_menu(food)
        )

    return (
        "Non ho ancora una risposta preparata per questa domanda. Posso aiutarti con menu, "
        "cocktail, contatti, indicazioni, eventi e prenotazioni."
    )
