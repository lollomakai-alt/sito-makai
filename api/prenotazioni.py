"""Dialogo prenotazioni: stato firmato, dati reali e conferma esplicita del cliente."""
import logging
import os
import re
import time
import unicodedata
from datetime import date, timedelta

from itsdangerous import BadSignature, URLSafeTimedSerializer

from bookings.dates import now_local
from bookings.service import active_for_phone, check_availability, create_booking
from bookings.validators import normalize_email, normalize_phone
from config import (CLOSED_WEEKDAYS, MAX_ACTIVE_PER_PHONE, MAX_ADVANCE_DAYS,
                    MAX_PARTY_SIZE, SLOT_START, SLOT_END, LOCAL_PHONE)
from chat_language import understand, people_count, intent

logger = logging.getLogger("makai")
SESSION_SECONDS = 1800
PHONE = LOCAL_PHONE or "339 751 4140"
DAYS = ("lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica")
QUESTIONS = {
    "persone": "Per quante persone?",
    "data": "Per che giorno? (es. domani, sabato, 12/10)",
    "ora": f"A che ora? (dalle {SLOT_START} alle {SLOT_END})",
    "nome": "Quali sono nome e cognome per la prenotazione?",
    "cognome": "Mi indichi anche il cognome?",
    "telefono": "Un numero di telefono? Lo usiamo per gestire la tua prenotazione.",
    "email": "Una email di riferimento per la prenotazione?",
    "email_confermata": "Confermi che l'email mostrata è corretta?",
    "note": "Hai richieste particolari (seggiolone, allergie)? Scrivi 'no' se non ne hai.",
    "consensi": "Prima del riepilogo puoi scegliere l'opzione privacy facoltativa.",
    "conferma": "Confermi il riepilogo? (sì/no)",
    "correggi": "Cosa vuoi cambiare? Persone, giorno, ora, nome, telefono, email, note o consensi? Oppure scrivi 'annulla'.",
}
FIELDS = {"persone": "persone", "persona": "persone", "giorno": "data", "data": "data",
          "ora": "ora", "orario": "ora", "nome": "nome", "telefono": "telefono",
          "numero": "telefono", "email": "email", "mail": "email", "note": "note",
          "consenso": "consensi", "consensi": "consensi", "ricordami": "consensi"}
PRIVACY_NOTICE = "Usiamo nome e telefono solo per gestire la prenotazione. Informativa: /privacy"


def normalize(text):
    # Keep date/time separators: 12/10 and 20:30 must survive normalization.
    text = unicodedata.normalize("NFKD", text.lower())
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip()


def has(text, words):
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def parse_persone(text):
    match = re.fullmatch(r"(?:siamo |per |in )?(\d{1,2})(?: persone| persona)?[.!]?", normalize(text))
    return int(match[1]) if match else None


def parse_data(text):
    text = normalize(text)
    today = now_local().date()
    for word, days in (("dopodomani", 2), ("domani", 1), ("oggi", 0)):
        if has(text, (word,)):
            return today + timedelta(days=days)
    iso = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    explicit = re.search(r"\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{4}|\d{2}))?\b", text)
    try:
        if iso:
            result = date(int(iso[1]), int(iso[2]), int(iso[3]))
            return result if result >= today else None
        if explicit:
            year = int(explicit[3]) if explicit[3] else today.year
            if year < 100:
                year += 2000
            result = date(year, int(explicit[2]), int(explicit[1]))
            if result < today and not explicit[3]:
                result = date(year + 1, int(explicit[2]), int(explicit[1]))
            return result if result >= today else None
    except ValueError:
        return None
    for weekday, name in enumerate(DAYS):
        if has(text, (name,)):
            return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)
    return None


def parse_ora(text):
    match = re.fullmatch(r"(?:(?:alle?|ore)\s+)?(\d{1,2})(?:[:.](\d{2}))?[.!]?", normalize(text))
    if not match:
        return None
    hour, minute = int(match[1]), int(match[2] or 0)
    if 1 <= hour <= 11:
        hour += 12
    return f"{hour:02d}:{minute:02d}" if hour < 24 and minute < 60 else None


def _serializer():
    secret = os.environ.get("CHAT_SESSION_SECRET") or os.environ.get("ADMIN_SESSION_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("Segreto sessioni chat non configurato.")
    return URLSafeTimedSerializer(secret, salt="makai-booking-chat-v1")


def _reply(text, state=None):
    return {"reply": text, "session_token": _serializer().dumps(state) if state else None}


def _summary(state):
    day = date.fromisoformat(state["data"]).strftime("%d/%m/%Y")
    return (f"Riepilogo: {state['persone']} persone, {day} alle {state['ora']}, "
            f"a nome {state['nome']}.\nTelefono: {state['telefono']}\nEmail: {state['email']}\n"
            f"Note: {state.get('note') or 'nessuna'}.\n"
            "Confermi? (sì/no). Puoi anche scrivere 'cambia' seguito dal campo da correggere.")


def _availability(state):
    return check_availability(state["data"], state["ora"], state["persone"])


def _unavailable(result):
    text = result.get("reason") or result.get("error") or "Nessun tavolo disponibile."
    if result.get("alternative_times"):
        text += " Orari alternativi: " + ", ".join(result["alternative_times"]) + "."
    return text


REQUIRED = (
    "persone", "data", "ora", "nome", "telefono", "email",
    "email_confermata", "note", "consensi",
)


def _advance(state, next_step=None):
    """Chiede soltanto i dati mancanti; la disponibilità non autorizza il salvataggio."""
    if all(key in state for key in ("persone", "data", "ora")):
        key = [state[k] for k in ("persone", "data", "ora")]
        if state.get("checked") != key:
            result = _availability(state)
            if not result["available"]:
                state.pop("ora", None)
                state["step"] = "ora"
                return _reply(_unavailable(result) + " Scegli un altro orario o scrivi 'cambia giorno'.", state)
            state["checked"] = key
        if state["mode"] == "availability":
            return _reply("Al momento c'è posto! Scrivi 'prenota' per iniziare: il tavolo non è ancora riservato.")
    next_step = next((field for field in REQUIRED if field not in state), "conferma")
    if next_step == "nome" and state.get("nome_parziale"):
        next_step = "cognome"
    state.pop("ritorno", None)
    state["step"] = next_step
    if next_step == "conferma":
        prompt = _summary(state)
    elif next_step == "email_confermata":
        prompt = f"È questa la tua email?\n{state['email']}\nConfermi?"
    else:
        prompt = QUESTIONS[next_step]
    personal_data_steps = (
        "nome", "cognome", "telefono", "email", "email_confermata", "note", "consensi",
    )
    if next_step in personal_data_steps and not state.get("privacy_notice_shown"):
        state["privacy_notice_shown"] = True
        prompt = PRIVACY_NOTICE + "\n\n" + prompt
    return _reply(prompt, state)


def _prefill(state, message):
    """Estrae dati espliciti da una frase, senza correggere nomi o contatti."""
    text = understand(message)
    count = people_count(text, bare=state["step"] == "persone")
    if count is not None and "persone" not in state:
        if not 1 <= count <= MAX_PARTY_SIZE:
            return f"Online si prenota da 1 a {MAX_PARTY_SIZE} persone. Per altri gruppi chiamaci al {PHONE}."
        state["persone"] = count
    date_error = None
    if "data" not in state:
        date_text = re.sub(r"\b(?:alle?|ore)\s+\d{1,2}(?:[:.]\d{2})?\b", "", text)
        day = parse_data(date_text)
        if day:
            error = _date_error(day)
            if error:
                date_error = error
            else:
                state["data"] = day.isoformat()
    if "ora" not in state:
        hour = re.search(r"\b(?:alle?|ore)\s+(\d{1,2}(?:[:.]\d{2})?)\b", text)
        if hour:
            value = parse_ora(hour[1])
            if value:
                state["ora"] = value
    if "email" not in state:
        email = re.search(r"[^\s,;]+@[^\s,;]+\.[a-zA-Z]{2,}", message)
        if email and normalize_email(email[0]):
            state["email"] = normalize_email(email[0])
    if "telefono" not in state:
        phone = next((m for m in re.finditer(r"(?<!\w)(?:\+|00)?\d[\d ()-]{7,}\d(?!\w)", message)
                      if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", m[0]) and normalize_phone(m[0])), None)
        if phone:
            value = normalize_phone(phone[0])
            if value is not None and active_for_phone(value) >= MAX_ACTIVE_PER_PHONE:
                return f"Questo numero ha già {MAX_ACTIVE_PER_PHONE} prenotazioni attive. Per altre chiamaci al {PHONE}."
            if value is not None:
                state["telefono"] = value
    if "nome" not in state:
        name = re.search(r"(?:mi chiamo|a nome|nome e cognome(?: sono)?)[ :]+(.+?)(?=,|;|\b(?:per|siamo|telefono|cellulare|email|mail|alle|ore)\b|$)", message, re.I)
        if name:
            value = name[1].strip(" .")
            if 2 <= len(value) <= 60 and re.fullmatch(r"[^\W\d_]+(?:[ '\-’][^\W\d_]+)+", value, re.UNICODE):
                state["nome"] = value
            elif 2 <= len(value) <= 60 and value.isalpha():
                state["nome_parziale"] = value
    return date_error


def _date_error(day):
    if day.weekday() in CLOSED_WEEKDAYS:
        return "Il lunedì siamo chiusi. Scegli un altro giorno."
    if day > now_local().date() + timedelta(days=MAX_ADVANCE_DAYS):
        return f"Si prenota al massimo {MAX_ADVANCE_DAYS} giorni prima."
    return None


def _is_information(text):
    return has(text, ("menu", "cocktail", "cucina", "orari", "aperti", "aprite", "chiudete",
                      "indirizzo", "dove siete", "dove si trova", "come arrivo", "eventi")) or text in (
                          "qual e il vostro telefono?", "qual e la vostra email?")


def _handle(state, message, info_fn, consenso_ricordami=False):
    text = understand(message)
    simple = text.strip(" .!?;:")
    step = state["step"]
    if simple in ("annulla", "annulla prenotazione", "annulla la prenotazione", "lascia stare", "non piu"):
        return _reply("Ok, nessuna prenotazione salvata da questa conversazione. Per ricominciare scrivi 'prenota'.")

    # Corrections are explicit; never interpret 'sì, ma...' as permission to save.
    if step == "correggi" or (has(text, ("cambia", "correggi", "modifica")) and step != "note"):
        complete = all(key in state for key in REQUIRED)
        if not complete:
            # Before the summary, only go back to a previously entered field.
            field = next((field for word, field in FIELDS.items() if has(text, (word,))), None)
            if field not in state:
                return _reply("Completiamo prima i dati. " + QUESTIONS[step], state)
        field = next((field for word, field in FIELDS.items() if has(text, (word,))), None)
        if field:
            state.pop(field, None)
            if field == "email":
                state.pop("email_confermata", None)
            state.update(step=field, ritorno=complete)
            return _reply(QUESTIONS[field], state)
        state["step"] = "correggi"
        return _reply(QUESTIONS["correggi"], state)

    is_email_value = step in ("email", "email_confermata") and "@" in message
    if _is_information(text) and not is_email_value:
        prompt = _summary(state) if step == "conferma" else QUESTIONS[step]
        return _reply((info_fn(message) or "Per questa informazione contatta il locale.") + "\n\nRiprendiamo: " + prompt, state)

    if step not in ("conferma", "correggi", "note", "cognome", "email", "email_confermata"):
        error = _prefill(state, message)
        if error:
            terminal = "da 1 a" in error or "prenotazioni attive" in error
            return _reply(error, None if terminal else state)
        if step in state and not state.get("ritorno"):
            return _advance(state)

    if step == "persone":
        number = parse_persone(text)
        if number is None or number < 1:
            return _reply(QUESTIONS[step], state)
        if number > MAX_PARTY_SIZE:
            return _reply(f"Sopra le {MAX_PARTY_SIZE} persone chiamaci al {PHONE}.")
        state["persone"] = number
        return _advance(state, "data")

    if step == "data":
        day = parse_data(text)
        if day is None:
            return _reply("Non ho capito il giorno. Prova con 'domani', 'sabato' o '12/10'.", state)
        error = _date_error(day)
        if error:
            return _reply(error, state)
        state["data"] = day.isoformat()
        return _advance(state, "ora")

    if step == "ora":
        hour = parse_ora(text)
        if hour is None:
            return _reply("Non ho capito l'orario. Scrivilo tipo 20:30.", state)
        state["ora"] = hour
        result = _availability(state)
        if not result["available"]:
            return _reply(_unavailable(result) + " Scegli un altro orario o scrivi 'cambia giorno'.", state)
        if state["mode"] == "availability":
            return _reply("Al momento c'è posto! Scrivi 'prenota' per iniziare: il tavolo non è ancora riservato.")
        response = _advance(state, "nome")
        response["reply"] = "Al momento c'è posto. " + response["reply"]
        return response

    if step == "nome":
        name = message.strip()
        if not 2 <= len(name) <= 60 or not re.fullmatch(r"[^\W\d_]+(?:[ '\-’][^\W\d_]+)*", name, re.UNICODE):
            return _reply("Scrivi il nome per la prenotazione (da 2 a 60 caratteri).", state)
        if len(name.split()) < 2:
            state["nome_parziale"] = name
            state["step"] = "cognome"
            return _reply(QUESTIONS["cognome"], state)
        state["nome"] = name
        return _advance(state, "telefono")

    if step == "cognome":
        surname = message.strip()
        full_name = state.get("nome_parziale", "") + " " + surname
        if not surname or len(full_name) > 60 or not re.fullmatch(r"[^\W\d_]+(?:[ '\-’][^\W\d_]+)*", surname, re.UNICODE):
            return _reply(QUESTIONS["cognome"], state)
        state["nome"] = full_name
        state.pop("nome_parziale", None)
        return _advance(state)


    if step == "telefono":
        phone = normalize_phone(message)
        if not phone:
            return _reply("Numero non valido, riprova con il prefisso internazionale.", state)
        if active_for_phone(phone) >= MAX_ACTIVE_PER_PHONE:
            return _reply(f"Questo numero ha già {MAX_ACTIVE_PER_PHONE} prenotazioni attive. Per altre chiamaci al {PHONE}.")
        state["telefono"] = phone
        return _advance(state, "email")

    if step == "email":
        email = normalize_email(message)
        if not email:
            return _reply("Scrivi solo l'indirizzo email completo, senza spazi o altre parole (esempio: nome@dominio.it).", state)
        state["email"] = email
        state.pop("email_confermata", None)
        return _advance(state, "email_confermata")

    if step == "email_confermata":
        if simple in ("si", "si confermo", "si, confermo", "confermo", "corretta", "esatto", "ok"):
            state["email_confermata"] = True
            return _advance(state, "note")
        if simple in ("no", "cambia", "cambia email", "non e corretta", "sbagliata"):
            state.pop("email", None)
            state.pop("email_confermata", None)
            state["step"] = "email"
            return _reply("Va bene, riscrivi l'email corretta.", state)
        replacement = normalize_email(message)
        if replacement:
            state["email"] = replacement
            state.pop("email_confermata", None)
            return _advance(state, "email_confermata")
        if "@" in message:
            return _reply("L'indirizzo inserito non è valido. Scrivi solo l'email completa, senza spazi o altre parole, oppure scegli “Cambia email”.", state)
        return _reply("Conferma con sì oppure scegli “Cambia email”.", state)

    if step == "note":
        if len(message.strip()) > 200:
            return _reply("Puoi riassumere le richieste in massimo 200 caratteri?", state)
        state["note"] = "" if simple in ("no", "niente", "nessuna", "nessuno", "nessuna nota") else message.strip()
        return _advance(state, "consensi")

    if step == "consensi":
        state["consenso_ricordami"] = bool(consenso_ricordami)
        state["consensi"] = True
        return _advance(state, "conferma")

    if step == "conferma":
        if simple in ("si", "si confermo", "si, confermo", "confermo", "ok", "va bene"):
            result = create_booking(
                name=state["nome"], email=state["email"], phone=state["telefono"],
                date=state["data"], time=state["ora"], party_size=state["persone"],
                notes=state.get("note", ""), request_started_at=state["started_at"],
                consenso_ricordami=state.get("consenso_ricordami", False),
            )
            if result["ok"]:
                day = date.fromisoformat(result["date"]).strftime("%d/%m/%Y")
                return _reply(f"Prenotazione confermata! {result['party_size']} persone, {day} alle {result['time']}, "
                              f"a nome {result['name']}. Per modifiche o cancellazioni chiamaci al {PHONE}.")
            if result.get("code") in ("phone_limit", "cancelled"):
                return _reply(result["error"] + f" Telefono: {PHONE}.")
            state.pop("ora", None)
            state.pop("checked", None)
            state.update(step="ora", ritorno=True)
            return _reply(_unavailable(result) + " Scegli un altro orario o scrivi 'cambia giorno'.", state)
        if simple in ("no", "non confermo"):
            state["step"] = "correggi"
            return _reply(QUESTIONS["correggi"], state)
        return _reply("Per salvare rispondi 'sì'. Per correggere scrivi 'no' o 'cambia' e il nome del campo.", state)

    return _reply("Ricominciamo: scrivi 'prenota' quando vuoi.")


def answer_booking(message, session_token, info_fn, consenso_ricordami=False):
    """None lascia la risposta alle FAQ. La cronologia del browser non autorizza scritture."""
    text = understand(message)
    wants_booking = intent(text) == "booking"
    wants_availability = has(text, ("disponibilita", "disponibile", "liberi", "libero", "posto", "posti", "tavolo"))
    if not session_token and not (wants_booking or wants_availability):
        return None
    # Existing bookings still require contact with staff, never email-only ownership.
    if not session_token and has(text, ("annulla", "annullare", "cancella", "cancellare", "modifica", "modificare")):
        return _reply(f"Per modificare o cancellare una prenotazione già salvata chiamaci al {PHONE}.")
    state = None
    try:
        signer = _serializer()
        if session_token:
            try:
                state = signer.loads(session_token, max_age=SESSION_SECONDS)
                if not isinstance(state, dict) or state.get("step") not in QUESTIONS:
                    raise BadSignature("Invalid booking state")
            except BadSignature:
                return _reply("La conversazione è scaduta o non è valida. Scrivi 'prenota' per ricominciare; "
                              "se avevi già confermato, contatta il locale prima di riprenotare.")
            return _handle(
                state,
                message,
                info_fn,
                consenso_ricordami=consenso_ricordami,
            )

        state = {"mode": "booking" if wants_booking else "availability", "step": "persone", "started_at": time.time()}
        error = _prefill(state, message)
        if error:
            terminal = "da 1 a" in error or "prenotazioni attive" in error
            if not terminal:
                state["step"] = next((field for field in REQUIRED if field not in state), "conferma")
            return _reply(error, None if terminal else state)
        return _advance(state)

    except Exception:
        # Never log the submitted contacts or announce success after a database error.
        logger.warning("Prenotazione chat non disponibile; nessuna conferma comunicata.")
        return {"reply": "Non riesco a verificare o salvare la prenotazione in questo momento. "
                         f"Riprova lo stesso messaggio o chiamaci al {PHONE}.",
                "session_token": session_token}
