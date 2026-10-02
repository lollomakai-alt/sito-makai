import logging
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Schemi Pydantic per le Richieste e Risposte ---

class ChatEventRequest(BaseModel):
    message: str
    session_token: Optional[str] = None
    consenso_ricordami: bool = False

class ChatEventResponse(BaseModel):
    reply: str
    session_token: str
    show_booking_consents: bool = False
    is_event_completed: bool = False
    quick_replies: Optional[List[str]] = None

# --- In-Memory Session Store per Eventi (o sostituibile con Redis/DB) ---

event_sessions: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(session_token: Optional[str]) -> tuple[str, Dict[str, Any]]:
    import uuid
    
    # Se il session_token è None o non esiste nello store, si forza il reset completo
    if not session_token or session_token not in event_sessions:
        token = str(uuid.uuid4())
        event_sessions[token] = {
            "step": "SELECT_TYPE",  # SELECT_TYPE, GUEST_COUNT, COMPLETED
            "event_type": None,     # "aperitivo", "cena", "dopocena"
            "guest_count": 0,
            "calculated_total": 0,
        }
        return token, event_sessions[token]
    
    return session_token, event_sessions[session_token]


# --- Logica Principale di Calcolo Preventivi Eventi ---

PRICING_MAP = {
    "aperitivo": 20,
    "cena": 35,
    "dopocena": 15,
}


def answer_event(message: str, context: Optional[Dict[str, Any]] = None, phone: str = "") -> str:
    """Risposta per il flusso eventi/feste usata dal chatbot principale.

    Il contesto viene aggiornato in-place perché la sessione firmata salva
    `context['event']` e i quick-replies derivano direttamente da quei campi.
    """
    event_context = (context or {}).setdefault("event", {})
    text = (message or "").lower().strip()
    if not text:
        return "Dimmi quale tipo di evento vuoi organizzare: aperitivo, cena / apericena o dopocena."

    if re.search(r"\b(?:nuovo|riprendi|ricomincia|reset|annulla)\b", text):
        event_context.clear()

    if re.search(r"\b(?:apericena|cena)\b", text) and "aperitivo" not in text:
        event_context["category"] = "cena / apericena"
        return (
            "Per le cene e l'apericena possiamo organizzare un evento in ambiente Tiki. "
            "Ti interessa un apericena o una cena più classica?"
        )

    if "aperitivo" in text:
        event_context["category"] = "aperitivo"
        return (
            "Per l'aperitivo organizziamo serate con cocktail e spazi conviviali. "
            "Per una stima precisa, dimmi quante persone ci saranno."
        )

    if "dopocena" in text or "dopo cena" in text:
        event_context["category"] = "dopo cena"
        event_context.pop("package", None)
        return (
            "Per il dopocena proponiamo tre formule: Drink + torta, Drink + snack e Drink + prosecco. "
            "Il servizio è disponibile dalle 22:30 alle 00:00 e chiude alle 02:00. "
            f"prenotazioni automatiche solo per la cena; per il dopocena contatta il locale al {phone} per confermare."
        )

    package_matches = {
        "drink + torta": "Drink + torta",
        "drink + snack": "Drink + snack",
        "drink + prosecco": "Drink + prosecco",
        "prosecco": "Drink + prosecco",
        "torta": "Drink + torta",
        "snack": "Drink + snack",
    }
    for recipe, label in package_matches.items():
        if recipe in text:
            event_context["package"] = label
            return (
                f"Ottimo: {label}. Per quante persone vuoi organizzare il servizio?"
            )

    people_match = re.search(r"\b(\d{1,2})\b", text)
    if people_match and event_context.get("package"):
        event_context["people"] = int(people_match.group(1))
        return (
            f"Perfetto, {int(people_match.group(1))} persone. Possiamo stilare un preventivo "
            "e ti aiuteremo a scegliere il miglior pacchetto per la tua serata."
        )

    if re.search(r"\b(?:festa|eventi|evento|compleanno|laurea|pacchetti)\b", text):
        return (
            "Per gli eventi del Makai proponiamo: Aperitivo, Cena / apericena e Dopocena. "
            "Se preferisci, ti posso aiutare a scegliere il formato giusto per la tua festa."
        )

    return (
        "Per organizzare un evento al Makai puoi scegliere tra Aperitivo, Cena / apericena e Dopocena. "
        "Dimmi il tipo di evento o il numero di ospiti e ti guidiamo nel pacchetto più adatto."
    )


def process_event_message(user_message: str, session: Dict[str, Any]) -> Dict[str, Any]:
    text = user_message.lower().strip()
    
    # Se la sessione era già in uno stato COMPLETED e si riparte con una richiesta evento, resetta il flusso locale
    if session.get("step") == "COMPLETED":
        session["step"] = "SELECT_TYPE"
        session["event_type"] = None
        session["guest_count"] = 0
        session["calculated_total"] = 0

    step = session.get("step", "SELECT_TYPE")

    # STEP 1: Selezione Tipo Evento (Aperitivo, Cena, Dopocena)
    if step == "SELECT_TYPE":
        if "apericena" in text or "aperitivo" in text:
            session["event_type"] = "aperitivo"
            session["step"] = "GUEST_COUNT"
            return {
                "reply": "Perfetto, per l'Aperitivo! Quanti ospiti sarete al party?",
                "quick_replies": ["10 persone", "20 persone", "30 persone", "50 persone"],
                "is_event_completed": False
            }
        elif "cena" in text:
            session["event_type"] = "cena"
            session["step"] = "GUEST_COUNT"
            return {
                "reply": "Ottima scelta! Per la Cena, quanti invitati prevedi?",
                "quick_replies": ["10 persone", "20 persone", "30 persone", "50 persone"],
                "is_event_completed": False
            }
        elif "dopocena" in text or "festa" in text:
            session["event_type"] = "dopocena"
            session["step"] = "GUEST_COUNT"
            return {
                "reply": "Ciurma pronti per la festa! Per il Dopocena, quanti sarete in totale?",
                "quick_replies": ["10 persone", "20 persone", "30 persone", "50 persone"],
                "is_event_completed": False
            }
        else:
            return {
                "reply": "Ahoy! Per organizzare al meglio il tuo evento o compleanno al Makai, dimmi prima la tipologia: preferisci Aperitivo, Cena o Dopocena?",
                "quick_replies": ["Aperitivo", "Cena", "Dopocena"],
                "is_event_completed": False
            }

    # STEP 2: Inserimento / Calcolo Numero Ospiti
    if step == "GUEST_COUNT":
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            count = int(numbers[0])
            if count > 0:
                session["guest_count"] = count
                event_type = session.get("event_type", "aperitivo")
                price_per_head = PRICING_MAP.get(event_type, 20)
                total = count * price_per_head
                session["calculated_total"] = total
                session["step"] = "COMPLETED"

                return {
                    "reply": f"Riepilogo preventivo per {count} persone ({event_type.capitalize()}):\n"
                             f"Totale stimato: €{total}.\n\n"
                             f"Vuoi procedere con la prenotazione o ricevere maggiori dettagli?",
                    "quick_replies": ["Vorrei prenotare un tavolo", "Calcola un nuovo preventivo"],
                    "is_event_completed": True
                }
        
        return {
            "reply": f"Per calcolare il preventivo per l'evento ({session.get('event_type')}), indicami il numero di persone (es. 20 persone).",
            "quick_replies": ["10 persone", "20 persone", "30 persone", "50 persone"],
            "is_event_completed": False
        }

    # Risposta di fallback generica
    return {
        "reply": "Vuoi calcolare un altro preventivo per un evento? Scegli il tipo di servizio: Aperitivo, Cena o Dopocena.",
        "quick_replies": ["Aperitivo", "Cena", "Dopocena"],
        "is_event_completed": True
    }


# --- Endpoint Handler (da usare con FastAPI o Serverless Function) ---

def handle_chat_events(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Funzione handler principale per l'API /api/chat o /api/chat_events
    """
    req = ChatEventRequest(**payload)
    
    # Recupera o azzera la sessione
    session_token, session = get_or_create_session(req.session_token)
    
    # Processa il messaggio e calcola il preventivo
    result = process_event_message(req.message, session)
    
    response = ChatEventResponse(
        reply=result["reply"],
        session_token=session_token,
        show_booking_consents=result.get("is_event_completed", False),
        is_event_completed=result.get("is_event_completed", False),
        quick_replies=result.get("quick_replies")
    )
    
    return response.dict()