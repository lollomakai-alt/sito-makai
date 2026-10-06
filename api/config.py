"""Configurazione condivisa e regole delle prenotazioni."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TZ = ZoneInfo("Europe/Rome")
# Stringa di connessione Supabase (Project Settings > Database > Session pooler)
DATABASE_URL = os.environ.get("DATABASE_URL")

# ===================== REGOLE DEL LOCALE (DA MODIFICARE) =====================
DINNER_BOOKING_START = "18:00"
DINNER_BOOKING_END = "23:00"
AFTER_DINNER_RESERVATION_START = "22:30"
AFTER_DINNER_RESERVATION_END = "00:00"
VENUE_CLOSE_TIME = "02:00"

# Alias mantenuti per compatibilità con il flusso esistente delle cene.
SLOT_START = DINNER_BOOKING_START
SLOT_END = DINNER_BOOKING_END
SLOT_MINUTES = 30           # intervallo delle alternative proposte
MAX_PARTY_SIZE = 6          # oltre questo numero è meglio chiamare il locale
MIN_ADVANCE_MINUTES = 30    # anticipo minimo per prenotare
MAX_ADVANCE_DAYS = 60       # anticipo massimo
CLOSED_WEEKDAYS = [0]       # lunedì chiuso
MAX_ACTIVE_PER_PHONE = 2    # prenotazioni future massime per telefono
RETENTION_DAYS = 30         # le prenotazioni vengono eliminate X giorni dopo la data
# ============================================================================

LOCAL_PHONE = os.environ.get("MAKAI_PHONE", "")  # telefono del locale, mostrato ai gruppi grandi
