"""Normalizzazione dei contatti e controlli sulle prenotazioni."""
import re
from datetime import timedelta

from config import (
    SLOT_START, SLOT_END, CLOSED_WEEKDAYS,
    MIN_ADVANCE_MINUTES, MAX_ADVANCE_DAYS, MAX_PARTY_SIZE, LOCAL_PHONE,
)
from .dates import now_local, _parse

def normalize_email(raw: str):
    """Compatta gli spazi e restituisce l'email in minuscolo, oppure None."""
    e = re.sub(r"\s+", "", raw or "").lower()
    if len(e) > 120 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", e):
        return None
    return e



def normalize_phone(raw: str):
    """Numero per richiamare il cliente a mano (anche fisso). None se non valido."""
    if not re.fullmatch(r"\+?[\d\s().-]+", (raw or "").strip()):
        return None
    s = re.sub(r"[^\d+]", "", raw or "")
    if s.startswith("00"):
        s = "+" + s[2:]
    digits = re.sub(r"\D", "", s)
    if not 8 <= len(digits) <= 15:
        return None
    if s.startswith("+"):
        return "+" + digits
    if digits.startswith("3") and len(digits) in (9, 10):
        return "+39" + digits  # cellulare italiano senza prefisso
    if digits.startswith("39") and len(digits) in (11, 12):
        return "+" + digits
    return digits



def _validate(date_str, time_str, party_size):
    dt = _parse(date_str, time_str)
    if not dt:
        return None, "Data o ora non valide (formato AAAA-MM-GG e HH:MM)."
    if not SLOT_START <= dt.strftime("%H:%M") <= SLOT_END:
        return None, f"Si prenota dalle {SLOT_START} alle {SLOT_END}."
    if dt.weekday() in CLOSED_WEEKDAYS:
        return None, "Quel giorno il locale è chiuso."
    now = now_local()
    if dt < now + timedelta(minutes=MIN_ADVANCE_MINUTES):
        return None, f"Servono almeno {MIN_ADVANCE_MINUTES} minuti di anticipo."
    if dt.date() > now.date() + timedelta(days=MAX_ADVANCE_DAYS):
        return None, f"Si può prenotare al massimo {MAX_ADVANCE_DAYS} giorni prima."
    if not isinstance(party_size, int) or not 1 <= party_size <= MAX_PARTY_SIZE:
        call = f" al {LOCAL_PHONE}" if LOCAL_PHONE else ""
        return None, f"Online si prenota fino a {MAX_PARTY_SIZE} persone. Per gruppi più numerosi è meglio chiamare il locale{call}."
    return dt, None
