"""Agenda prenotazioni del Makai: database Supabase (Postgres) + funzioni usate da Gemini.

Le funzioni pubbliche con docstring (check_availability, create_booking,
find_bookings, modify_booking, cancel_booking) vengono passate a Gemini come
"tools": la docstring serve al modello per capire come usarle.
"""
import os
import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    import psycopg
    from psycopg.rows import dict_row
except ModuleNotFoundError:  # La chat FAQ locale funziona anche senza Supabase.
    psycopg = None
    dict_row = None

TZ = ZoneInfo("Europe/Rome")
# Stringa di connessione Supabase (Project Settings > Database > Session pooler)
DATABASE_URL = os.environ.get("DATABASE_URL")
_LOCK_ID = 734512  # serializza le scritture: due clienti non prendono lo stesso tavolo

# ===================== REGOLE DEL LOCALE (DA MODIFICARE) =====================
SLOT_START = "18:00"        # primo orario prenotabile
SLOT_END = "23:30"          # ultimo orario prenotabile
SLOT_MINUTES = 30           # ogni quanti minuti c'è uno slot
MAX_PARTY_SIZE = 6          # oltre questo numero è meglio chiamare il locale
STAY_MINUTES = 120          # durata stimata di una prenotazione
MIN_ADVANCE_MINUTES = 60    # anticipo minimo per prenotare
MAX_ADVANCE_DAYS = 60       # anticipo massimo
CLOSED_WEEKDAYS = []        # giorni di chiusura: 0=lunedì ... 6=domenica
MAX_ACTIVE_PER_EMAIL = 3    # prenotazioni future massime per email
REMINDER_HOURS = 4          # promemoria via email X ore prima
MAX_REMINDER_ATTEMPTS = 5
RETENTION_DAYS = 30         # le prenotazioni vengono eliminate X giorni dopo la data
# ============================================================================

LOCAL_PHONE = os.environ.get("MAKAI_PHONE", "")  # telefono del locale, mostrato ai gruppi grandi

# ======================= SALA: TAVOLI E POSTI =======================
TABLES = {            # id tavolo: numero di posti
    # Sala principale
    "10": 3, "11": 3, "12": 2, "13": 2,
    "14": 2, "15": 4, "16": 4, "17": 2, "18": 4, "19": 4,
    # Sala piccola
    "20": 4, "21": 4, "22": 2, "23": 2,
}

# File di tavoli ADIACENTI che si possono unire, nell'ordine in cui sono disposti.
# Si uniscono solo tavoli vicini della stessa fila (es. 10+11, 11+12, 10+11+12...).
JOINABLE_ROWS = [
    ["10", "11", "12", "13"],
    ["14", "15", "16", "17", "18", "19"],
    ["21", "22", "23"],
]

# Non unire tavoli se i posti totali superano questo valore
# (i posti di una unione = somma dei posti dei singoli tavoli)
MAX_COMBO_SEATS = 8
# ====================================================================


def _check_config():
    for row in JOINABLE_ROWS:
        for t in row:
            if t not in TABLES:
                raise ValueError(f"JOINABLE_ROWS: il tavolo '{t}' non esiste in TABLES")


def _build_combinations():
    combos = []
    for row in JOINABLE_ROWS:
        for i in range(len(row)):
            for j in range(i + 2, len(row) + 1):
                ids = row[i:j]
                seats = sum(TABLES[t] for t in ids)
                if seats <= MAX_COMBO_SEATS:
                    combos.append((ids, seats))
    return combos


_check_config()
COMBINATIONS = _build_combinations()


def now_local() -> datetime:
    return datetime.now(TZ)


@contextmanager
def db(write: bool = False):
    if psycopg is None:
        raise RuntimeError("Installa psycopg per usare le prenotazioni Supabase.")
    if not DATABASE_URL:
        raise RuntimeError("Manca la variabile DATABASE_URL (stringa di connessione di Supabase).")
    conn = psycopg.connect(
        DATABASE_URL, row_factory=dict_row, prepare_threshold=None, connect_timeout=10
    )
    try:
        if write:
            conn.execute(f"SELECT pg_advisory_xact_lock({_LOCK_ID})")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Controlla che la tabella esista. Si crea UNA volta con crea_tabelle.sql su Supabase."""
    with db(write=True) as c:
        if not c.execute("SELECT to_regclass('public.bookings') AS t").fetchone()["t"]:
            raise RuntimeError(
                "La tabella 'bookings' non esiste: esegui crea_tabelle.sql nel SQL Editor di Supabase."
            )
        # se il server si era fermato durante un invio, riprova
        c.execute("UPDATE bookings SET reminder_status='pending' WHERE reminder_status='sending'")


def purge_old_bookings() -> int:
    """Elimina le prenotazioni la cui data è più vecchia di RETENTION_DAYS giorni."""
    limit = (now_local() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    with db(write=True) as c:
        return c.execute("DELETE FROM bookings WHERE booking_date < %s", (limit,)).rowcount


# ------------------------------- utilità ------------------------------------
def normalize_email(raw: str):
    """Restituisce l'email in minuscolo se sembra valida, altrimenti None."""
    e = (raw or "").strip().lower()
    if len(e) > 120 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", e):
        return None
    return e


def normalize_phone(raw: str):
    """Numero per richiamare il cliente a mano (anche fisso). None se non valido."""
    s = re.sub(r"[^\d+]", "", raw or "")
    if s.startswith("00"):
        s = "+" + s[2:]
    digits = re.sub(r"\D", "", s)
    if not 6 <= len(digits) <= 15:
        return None
    if s.startswith("+"):
        return "+" + digits
    if digits.startswith("3") and len(digits) in (9, 10):
        return "+39" + digits  # cellulare italiano senza prefisso
    return digits


def _parse(date_str: str, time_str: str):
    try:
        d = datetime.strptime((date_str or "").strip(), "%Y-%m-%d")
        t = datetime.strptime((time_str or "").strip(), "%H:%M")
    except ValueError:
        return None
    return datetime.combine(d.date(), t.time(), tzinfo=TZ)


def _slots():
    cur = datetime.strptime(SLOT_START, "%H:%M")
    end = datetime.strptime(SLOT_END, "%H:%M")
    out = []
    while cur <= end:
        out.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=SLOT_MINUTES)
    return out


def _validate(date_str, time_str, party_size):
    dt = _parse(date_str, time_str)
    if not dt:
        return None, "Data o ora non valide (formato AAAA-MM-GG e HH:MM)."
    if dt.strftime("%H:%M") not in _slots():
        return None, f"Si prenota dalle {SLOT_START} alle {SLOT_END}, ogni {SLOT_MINUTES} minuti."
    if dt.weekday() in CLOSED_WEEKDAYS:
        return None, "Quel giorno il locale è chiuso."
    now = now_local()
    if dt < now + timedelta(minutes=MIN_ADVANCE_MINUTES):
        return None, f"Servono almeno {MIN_ADVANCE_MINUTES} minuti di anticipo."
    if dt > now + timedelta(days=MAX_ADVANCE_DAYS):
        return None, f"Si può prenotare al massimo {MAX_ADVANCE_DAYS} giorni prima."
    if not isinstance(party_size, int) or not 1 <= party_size <= MAX_PARTY_SIZE:
        call = f" al {LOCAL_PHONE}" if LOCAL_PHONE else ""
        return None, f"Online si prenota fino a {MAX_PARTY_SIZE} persone. Per gruppi più numerosi è meglio chiamare il locale{call}."
    return dt, None


def _reminder_status_for(dt: datetime) -> str:
    # se si prenota a meno di X ore dall'arrivo, il promemoria non ha senso
    return "skipped" if dt - now_local() <= timedelta(hours=REMINDER_HOURS) else "pending"


def _units():
    """Tutte le sistemazioni possibili: singoli tavoli + combinazioni ammesse."""
    units = [([t], seats) for t, seats in TABLES.items()]
    units += [(list(ids), seats) for ids, seats in COMBINATIONS]
    return units


def _occupied_tables(c, dt: datetime, exclude_id=None) -> set:
    rows = c.execute(
        "SELECT id, booking_date, booking_time, tables FROM bookings "
        "WHERE booking_date=%s AND status='confirmed'",
        (dt.strftime("%Y-%m-%d"),),
    ).fetchall()
    busy = set()
    for r in rows:
        if exclude_id is not None and r["id"] == exclude_id:
            continue
        other = _parse(r["booking_date"], r["booking_time"])
        if other and abs((other - dt).total_seconds()) < STAY_MINUTES * 60:
            busy.update(t for t in r["tables"].split(",") if t)
    return busy


def _find_tables(c, dt: datetime, party_size: int, exclude_id=None):
    """Tavolo (o combinazione) libero che spreca meno posti. Lista di id, oppure None."""
    busy = _occupied_tables(c, dt, exclude_id)
    best = None
    for ids, seats in _units():
        if seats < party_size or busy.intersection(ids):
            continue
        key = (seats, len(ids))  # meno posti sprecati, poi meno tavoli uniti
        if best is None or key < best[0]:
            best = (key, ids)
    return best[1] if best else None


def _alternatives(c, dt: datetime, party_size: int, exclude_id=None):
    now = now_local()
    options = []
    for slot in _slots():
        cand = _parse(dt.strftime("%Y-%m-%d"), slot)
        if cand < now + timedelta(minutes=MIN_ADVANCE_MINUTES):
            continue
        if _find_tables(c, cand, party_size, exclude_id) is not None:
            options.append((abs((cand - dt).total_seconds()), slot))
    options.sort()
    return [slot for _, slot in options[:3]]


def _upcoming_for_email(c, email: str):
    rows = c.execute(
        "SELECT * FROM bookings WHERE email=%s AND status='confirmed' "
        "ORDER BY booking_date, booking_time",
        (email,),
    ).fetchall()
    now = now_local()
    return [r for r in rows if (_parse(r["booking_date"], r["booking_time"]) or now) > now]


def _get_owned(c, booking_id, email):
    return c.execute(
        "SELECT * FROM bookings WHERE id=%s AND email=%s AND status='confirmed'",
        (booking_id, email),
    ).fetchone()


# ------------------ TOOL PER GEMINI (le docstring contano!) -----------------
def check_availability(date: str, time: str, party_size: int) -> dict:
    """Verifica se c'è posto al Makai per data, ora e numero di persone.

    Args:
        date: data in formato AAAA-MM-GG (es. 2026-10-03).
        time: orario in formato HH:MM a 24 ore (es. 21:00).
        party_size: numero di persone.
    """
    dt, err = _validate(date, time, party_size)
    if err:
        return {"available": False, "reason": err}
    with db() as c:
        if _find_tables(c, dt, party_size) is not None:
            return {"available": True}
        return {
            "available": False,
            "reason": "Non c'è posto a quell'orario.",
            "alternative_times": _alternatives(c, dt, party_size),
        }


def create_booking(name: str, email: str, phone: str, date: str, time: str, party_size: int, notes: str = "") -> dict:
    """Crea una prenotazione. Chiamala SOLO dopo che il cliente ha confermato il riepilogo.

    Args:
        name: nome per la prenotazione.
        email: email del cliente (per il promemoria).
        phone: numero di telefono del cliente (il locale lo usa per contattarlo in caso di necessità).
        date: data in formato AAAA-MM-GG.
        time: orario in formato HH:MM a 24 ore.
        party_size: numero di persone.
        notes: richieste particolari (facoltativo).
    """
    name = (name or "").strip()[:60]
    if len(name) < 2:
        return {"ok": False, "error": "Serve il nome per la prenotazione."}
    p = normalize_email(email)
    if not p:
        return {"ok": False, "error": "Email non valida."}
    ph = normalize_phone(phone)
    if not ph:
        return {"ok": False, "error": "Numero di telefono non valido."}
    dt, err = _validate(date, time, party_size)
    if err:
        return {"ok": False, "error": err}

    with db(write=True) as c:
        if len(_upcoming_for_email(c, p)) >= MAX_ACTIVE_PER_EMAIL:
            return {"ok": False, "error": f"Questa email ha già {MAX_ACTIVE_PER_EMAIL} prenotazioni attive."}
        assigned = _find_tables(c, dt, party_size)
        if not assigned:
            return {
                "ok": False,
                "error": "Non c'è più posto a quell'orario.",
                "alternative_times": _alternatives(c, dt, party_size),
            }
        cur = c.execute(
            "INSERT INTO bookings (name, email, phone, booking_date, booking_time, party_size, notes, "
            "reminder_status, tables) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (name, p, ph, dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"), party_size,
             (notes or "").strip()[:300], _reminder_status_for(dt),
             ",".join(assigned)),
        )
        return {
            "ok": True,
            "booking_id": cur.fetchone()["id"],
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "party_size": party_size,
        }


def find_bookings(email: str) -> dict:
    """Elenca le prenotazioni future di un cliente, cercandole per email.

    Args:
        email: email usata per la prenotazione.
    """
    p = normalize_email(email)
    if not p:
        return {"ok": False, "error": "Email non valida."}
    with db() as c:
        rows = _upcoming_for_email(c, p)
    return {
        "ok": True,
        "bookings": [
            {"booking_id": r["id"], "name": r["name"], "date": r["booking_date"],
             "time": r["booking_time"], "party_size": r["party_size"]}
            for r in rows
        ],
    }


def modify_booking(booking_id: int, email: str, date: str, time: str, party_size: int) -> dict:
    """Modifica data, ora o persone di una prenotazione. Chiamala SOLO dopo conferma del cliente.

    Args:
        booking_id: numero della prenotazione.
        email: email con cui è stata fatta.
        date: nuova data AAAA-MM-GG (o quella attuale se non cambia).
        time: nuovo orario HH:MM (o quello attuale se non cambia).
        party_size: nuovo numero di persone (o quello attuale se non cambia).
    """
    p = normalize_email(email)
    if not p:
        return {"ok": False, "error": "Email non valida."}
    dt, err = _validate(date, time, party_size)
    if err:
        return {"ok": False, "error": err}
    with db(write=True) as c:
        row = _get_owned(c, booking_id, p)
        if not row:
            return {"ok": False, "error": "Prenotazione non trovata per questa email."}
        assigned = _find_tables(c, dt, party_size, exclude_id=booking_id)
        if not assigned:
            return {
                "ok": False,
                "error": "Non c'è posto a quell'orario.",
                "alternative_times": _alternatives(c, dt, party_size, exclude_id=booking_id),
            }
        c.execute(
            "UPDATE bookings SET booking_date=%s, booking_time=%s, party_size=%s, tables=%s, "
            "reminder_status=%s, reminder_attempts=0 WHERE id=%s",
            (dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"), party_size, ",".join(assigned),
             _reminder_status_for(dt), booking_id),
        )
        return {"ok": True, "booking_id": booking_id, "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M"), "party_size": party_size}


def cancel_booking(booking_id: int, email: str) -> dict:
    """Cancella una prenotazione. Chiamala SOLO dopo conferma del cliente.

    Args:
        booking_id: numero della prenotazione.
        email: email con cui è stata fatta.
    """
    p = normalize_email(email)
    if not p:
        return {"ok": False, "error": "Email non valida."}
    with db(write=True) as c:
        if not _get_owned(c, booking_id, p):
            return {"ok": False, "error": "Prenotazione non trovata per questa email."}
        c.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (booking_id,))
        return {"ok": True, "booking_id": booking_id}


# ------------------------------ ADMIN / AGENDA ------------------------------
def list_day(date_str: str):
    with db() as c:
        rows = c.execute(
            "SELECT id, name, email, phone, tables, booking_date, booking_time, party_size, notes, status, reminder_status "
            "FROM bookings WHERE booking_date=%s ORDER BY booking_time",
            (date_str,),
        ).fetchall()
    return [dict(r) for r in rows]


def admin_cancel(booking_id: int) -> bool:
    with db(write=True) as c:
        cur = c.execute(
            "UPDATE bookings SET status='cancelled' WHERE id=%s AND status='confirmed'", (booking_id,)
        )
        return cur.rowcount == 1


# ------------------------------- PROMEMORIA ---------------------------------
def due_reminders():
    """Prenotazioni confermate che iniziano tra 0 e REMINDER_HOURS ore e non sono ancora state avvisate."""
    now = now_local()
    with db() as c:
        rows = c.execute(
            "SELECT * FROM bookings WHERE status='confirmed' AND reminder_status='pending' "
            "AND booking_date BETWEEN %s AND %s",
            (now.strftime("%Y-%m-%d"), (now + timedelta(days=1)).strftime("%Y-%m-%d")),
        ).fetchall()
    due, expired = [], []
    for r in rows:
        dt = _parse(r["booking_date"], r["booking_time"])
        if dt is None:
            continue
        if dt <= now:
            expired.append(r["id"])
        elif dt - now <= timedelta(hours=REMINDER_HOURS):
            due.append(dict(r))
    if expired:  # prenotazioni ormai passate senza avviso (es. server spento)
        with db(write=True) as c:
            c.execute("UPDATE bookings SET reminder_status='skipped' WHERE id = ANY(%s)", (expired,))
    return due


def claim_reminder(booking_id: int) -> bool:
    """Blocca l'invio per questo processo (evita doppi messaggi con più worker)."""
    with db(write=True) as c:
        cur = c.execute(
            "UPDATE bookings SET reminder_status='sending' WHERE id=%s AND reminder_status='pending'",
            (booking_id,),
        )
        return cur.rowcount == 1


def finish_reminder(booking_id: int, ok: bool):
    with db(write=True) as c:
        if ok:
            c.execute("UPDATE bookings SET reminder_status='sent' WHERE id=%s", (booking_id,))
        else:
            c.execute(
                "UPDATE bookings SET reminder_attempts=reminder_attempts+1, "
                "reminder_status=CASE WHEN reminder_attempts+1>=%s THEN 'failed' ELSE 'pending' END "
                "WHERE id=%s",
                (MAX_REMINDER_ATTEMPTS, booking_id),
            )
