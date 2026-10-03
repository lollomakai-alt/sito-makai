"""Operazioni sulle prenotazioni e agenda del gestore."""
import re
import unicodedata

from config import MAX_ACTIVE_PER_PHONE
from database import db
from .dates import now_local, _parse
from .validators import normalize_email, normalize_phone, normalize_booking_name, _validate
from .tables import _find_tables, _alternatives
from .occupancy import valid_assignment

MARKETING_CONSENT_TEXT = (
    "Ti va di ricevere di tanto in tanto su WhatsApp offerte, sconti speciali, "
    "novità ed eventi riservati alla ciurma del Makai, compresi un pensiero per "
    "il compleanno e iniziative legate alle visite? La scelta è facoltativa, non "
    "cambia la prenotazione e può essere revocata. Basta rispondere Sì o Confermo."
)
MARKETING_CONSENT_VERSION = "2026-10-01-v3"
PRIVACY_VERSION = "2026-10-01"


def _is_explicit_marketing_yes(response_text: str) -> bool:
    normalized = unicodedata.normalize("NFKD", response_text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    if re.search(r"\b(?:no|non|rifiuto)\b", normalized):
        return False
    return bool(re.match(r"^(?:si|confermo|accetto)(?:\b|$)", normalized))

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



def _upcoming_for_phone(c, phone):
    # Normalize legacy numbers too: +39, 0039 and local mobile forms are equivalent.
    now = now_local()
    rows = c.execute(
        "SELECT phone, booking_date, booking_time FROM bookings "
        "WHERE status='confirmed' AND booking_date >= %s",
        (now.strftime("%Y-%m-%d"),),
    ).fetchall()
    return [r for r in rows if normalize_phone(r["phone"]) == phone
            and (_parse(r["booking_date"], r["booking_time"]) or now) > now]


def active_for_phone(phone: str) -> int:
    normalized = normalize_phone(phone)
    if not normalized:
        raise ValueError("Numero di telefono non valido.")
    with db() as c:
        return len(_upcoming_for_phone(c, normalized))


def create_booking(name: str, email: str, phone: str, date: str, time: str,
                   party_size: int, notes: str = "", request_started_at=None,
                   consenso_ricordami: bool = False) -> dict:
    """Salva solo dopo il sì al riepilogo; verifica limiti e tavoli nella transazione.

    request_started_at proviene dalla sessione firmata dal server: permette di
    riconoscere un reinvio della stessa conferma, anche su processi diversi.
    """
    name = normalize_booking_name(name)
    if not name:
        return {"ok": False, "error": "Inserisci nome e cognome, senza numeri o simboli."}
    p = normalize_email(email)
    if not p:
        return {"ok": False, "error": "Email non valida."}
    ph = normalize_phone(phone)
    if not ph:
        return {"ok": False, "error": "Numero di telefono non valido."}
    notes = (notes or "").strip()[:300]
    consenso_ricordami = bool(consenso_ricordami)

    with db(write=True) as c:
        # Read under the same write lock as the insert. A lost HTTP response must
        # not create a second booking when the client retries its signed request.
        if request_started_at is not None:
            previous = c.execute(
                "SELECT id, name, booking_date, booking_time, party_size, status, tables FROM bookings "
                "WHERE name=%s AND email=%s AND phone=%s AND booking_date=%s "
                "AND booking_time=%s AND party_size=%s AND notes=%s "
                "AND created_at >= to_timestamp(%s) ORDER BY id LIMIT 1",
                (name, p, ph, date, time, party_size, notes, request_started_at),
            ).fetchone()
            if previous:
                if previous["status"] != "confirmed":
                    return {"ok": False, "code": "cancelled", "error":
                            "Questa richiesta è stata annullata. Contatta il locale per riprenotare."}
                if not valid_assignment(previous.get("tables"), previous["party_size"]):
                    return {"ok": False, "code": "table_unassigned", "error":
                            "Prenotazione esistente con TAVOLO DA ASSEGNARE. Contatta il locale."}
                return {"ok": True, "booking_id": previous["id"], "name": previous["name"],
                        "date": previous["booking_date"], "time": previous["booking_time"],
                        "party_size": previous["party_size"]}
        if c.execute(
            "SELECT 1 FROM public.online_booking_closures WHERE booking_date::text=%s", (date,),
        ).fetchone():
            return {"ok": False, "code": "online_closed", "error":
                    "Le prenotazioni online per questo giorno sono chiuse. Contatta il locale."}
        dt, err = _validate(date, time, party_size)
        if err:
            return {"ok": False, "error": err}
        if len(_upcoming_for_phone(c, ph)) >= MAX_ACTIVE_PER_PHONE:
            return {"ok": False, "code": "phone_limit", "error":
                    f"Questo telefono ha già {MAX_ACTIVE_PER_PHONE} prenotazioni attive. Per altre chiamaci."}
        assigned = _find_tables(c, dt, party_size)
        if not assigned or not valid_assignment(",".join(assigned), party_size):
            return {"ok": False, "error": "Non c'è più posto a quell'orario.",
                    "alternative_times": _alternatives(c, dt, party_size)}
        cur = c.execute(
            "INSERT INTO bookings (name, email, phone, booking_date, booking_time, party_size, notes, "
            "tables, status, source, reminder_status, consenso_ricordami, consenso_data) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'confirmed','booking','skipped',%s,"
            "CASE WHEN %s THEN now() ELSE NULL END) RETURNING id",
            (name, p, ph, dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"), party_size,
             notes, ",".join(assigned), consenso_ricordami, consenso_ricordami),
        )
        booking_id = cur.fetchone()["id"]
        return {"ok": True, "booking_id": booking_id, "name": name,
                "date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M"),
                "party_size": party_size}


def create_admin_booking(name: str, phone: str, date: str, time: str,
                         party_size: int, email: str = "", notes: str = "") -> dict:
    """Inserisce una prenotazione ricevuta dal gestore, senza acquisire consensi."""
    name = normalize_booking_name(name)
    if not name:
        return {"ok": False, "error": "Inserisci nome e cognome, senza numeri o simboli."}

    ph = normalize_phone(phone)
    if not ph:
        return {"ok": False, "error": "Numero di telefono non valido."}

    raw_email = (email or "").strip()
    normalized_email = normalize_email(raw_email) if raw_email else ""
    if raw_email and not normalized_email:
        return {"ok": False, "error": "Email non valida."}

    notes = (notes or "").strip()
    if len(notes) > 300:
        return {"ok": False, "error": "Le note possono contenere al massimo 300 caratteri."}
    if type(party_size) is not int:
        return {"ok": False, "error": "Il numero di persone deve essere intero."}
    dt, err = _validate(date, time, party_size)
    if err:
        return {"ok": False, "error": err}
    if not re.fullmatch(r"[0-9]{2}:(?:00|30)", time):
        return {"ok": False, "error": "Scegli un orario a intervalli di 30 minuti."}
    with db(write=True) as c:
        if len(_upcoming_for_phone(c, ph)) >= MAX_ACTIVE_PER_PHONE:
            return {"ok": False, "code": "phone_limit", "error":
                    f"Questo telefono ha già {MAX_ACTIVE_PER_PHONE} prenotazioni attive."}
        assigned = _find_tables(c, dt, party_size)
        if not assigned or not valid_assignment(",".join(assigned), party_size):
            return {"ok": False, "error": "Non c'è più posto a quell'orario.",
                    "alternative_times": _alternatives(c, dt, party_size)}

        cur = c.execute(
            "INSERT INTO bookings (name, email, phone, booking_date, booking_time, party_size, notes, "
            "tables, status, source, reminder_status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'confirmed','agenda','skipped') RETURNING id",
            (name, normalized_email, ph, dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"),
             party_size, notes, ",".join(assigned)),
        )
        booking_id = cur.fetchone()["id"]
        return {"ok": True, "booking_id": booking_id, "name": name,
                "date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M"),
                "party_size": party_size}



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
        if not assigned or not valid_assignment(",".join(assigned), party_size):
            return {
                "ok": False,
                "error": "Non c'è posto a quell'orario.",
                "alternative_times": _alternatives(c, dt, party_size, exclude_id=booking_id),
            }
        c.execute(
            "UPDATE bookings SET booking_date=%s, booking_time=%s, party_size=%s, tables=%s WHERE id=%s",
            (dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"), party_size, ",".join(assigned),
             booking_id),
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



def list_day(date_str: str):
    with db() as c:
        rows = c.execute(
            "SELECT b.id, b.name, b.email, b.phone, b.tables, b.booking_date, b.booking_time, "
            "b.party_size, b.notes, b.status, b.source, b.arrived_at, "
            "mc.consenso_data AS marketing_consented_at, "
            "mc.scadenza_consenso AS marketing_expires_at, mc.revocato_il AS marketing_revoked_at, "
            "COALESCE(mc.visite_totali, 0) AS marketing_visit_count, mc.ultima_visita, "
            "CASE WHEN mc.id IS NOT NULL AND mc.revocato_il IS NULL "
            "AND mc.scadenza_consenso > now() THEN true ELSE false END AS marketing_consent_active "
            "FROM bookings b LEFT JOIN LATERAL ("
            "SELECT m.id, m.consenso_data, m.scadenza_consenso, m.revocato_il, "
            "m.visite_totali, m.ultima_visita "
            "FROM marketing_contacts m WHERE m.phone=b.phone "
            "OR (b.email <> '' AND m.email IS NOT NULL AND lower(m.email)=lower(b.email)) "
            "ORDER BY (m.phone=b.phone) DESC, m.consenso_data DESC LIMIT 1"
            ") mc ON true WHERE b.booking_date=%s ORDER BY b.booking_time",
            (date_str,),
        ).fetchall()
    result = [dict(r) for r in rows]
    for booking in result:
        missing = booking["status"] == "confirmed" and not (booking["tables"] or "").strip()
        booking["table_assignment_warning"] = "TAVOLO DA ASSEGNARE" if missing else None
    return result


def register_marketing_consent(booking_id: int, channel: str, response_text: str,
                               recorded_by: str) -> dict:
    """Registra o rinnova per 24 mesi un consenso esplicito ricevuto dallo staff."""
    if channel not in {"whatsapp", "telefono", "email"}:
        return {"ok": False, "error": "Canale del consenso non valido."}
    response_text = (response_text or "").strip()[:200]
    if not response_text:
        return {"ok": False, "error": "Inserisci la risposta positiva del cliente."}
    if not _is_explicit_marketing_yes(response_text):
        return {"ok": False, "error": "Per registrare il consenso la risposta deve iniziare con Sì, Confermo o Accetto. Grazie da solo non basta."}

    with db(write=True) as c:
        booking = c.execute(
            "SELECT id, name, email, phone, arrived_at, marketing_visit_counted_at FROM bookings "
            "WHERE id=%s AND status='confirmed' AND source='agenda'",
            (booking_id,),
        ).fetchone()
        if not booking:
            return {"ok": False, "error": "Prenotazione manuale non trovata."}

        existing = c.execute(
            "SELECT id FROM marketing_contacts WHERE phone=%s "
            "OR (%s <> '' AND email IS NOT NULL AND lower(email)=lower(%s)) "
            "ORDER BY (phone=%s) DESC LIMIT 1 FOR UPDATE",
            (booking["phone"], booking["email"], booking["email"], booking["phone"]),
        ).fetchone()

        values = (
            booking["name"], booking["email"], booking["phone"], booking["id"], channel,
            MARKETING_CONSENT_TEXT, MARKETING_CONSENT_VERSION, PRIVACY_VERSION,
            response_text, (recorded_by or "admin")[:100],
        )
        if existing:
            row = c.execute(
                "UPDATE marketing_contacts SET nome=%s, "
                "email=COALESCE(NULLIF(%s,''), email), phone=%s, booking_id=%s, canale=%s, "
                "consenso_testo=%s, consenso_versione=%s, privacy_versione=%s, risposta=%s, "
                "consenso_data=now(), scadenza_consenso=now()+interval '24 months', "
                "revocato_il=NULL, rinnovi=rinnovi+1, registrato_da=%s, updated_at=now() "
                "WHERE id=%s RETURNING id, consenso_data, scadenza_consenso, rinnovi, visite_totali",
                values + (existing["id"],),
            ).fetchone()
        else:
            row = c.execute(
                "INSERT INTO marketing_contacts (nome, email, phone, booking_id, canale, "
                "consenso_testo, consenso_versione, privacy_versione, risposta, consenso_data, "
                "scadenza_consenso, revocato_il, rinnovi, registrato_da, fonte, updated_at) "
                "VALUES (%s,NULLIF(%s,''),%s,%s,%s,%s,%s,%s,%s,now(),"
                "now()+interval '24 months',NULL,1,%s,'agenda',now()) "
                "RETURNING id, consenso_data, scadenza_consenso, rinnovi, visite_totali",
                values,
            ).fetchone()

        visits = row["visite_totali"]
        if booking["arrived_at"] and not booking["marketing_visit_counted_at"]:
            counted = c.execute(
                "UPDATE marketing_contacts SET visite_totali=visite_totali+1, ultima_visita=%s, "
                "updated_at=now() WHERE id=%s RETURNING visite_totali",
                (booking["arrived_at"], row["id"]),
            ).fetchone()
            c.execute(
                "UPDATE bookings SET marketing_visit_counted_at=now() "
                "WHERE id=%s AND marketing_visit_counted_at IS NULL",
                (booking["id"],),
            )
            visits = counted["visite_totali"]

    return {"ok": True, "consent_id": row["id"], "consented_at": row["consenso_data"],
            "expires_at": row["scadenza_consenso"], "renewals": row["rinnovi"],
            "visits": visits}


def revoke_marketing_consent(booking_id: int, recorded_by: str) -> bool:
    """Revoca il contatto collegato alla prenotazione e blocca subito il marketing."""
    with db(write=True) as c:
        booking = c.execute(
            "SELECT email, phone FROM bookings WHERE id=%s", (booking_id,)
        ).fetchone()
        if not booking:
            return False
        cur = c.execute(
            "UPDATE marketing_contacts SET revocato_il=now(), registrato_da=%s, updated_at=now() "
            "WHERE revocato_il IS NULL AND (phone=%s OR "
            "(%s <> '' AND email IS NOT NULL AND lower(email)=lower(%s)))",
            ((recorded_by or "admin")[:100], booking["phone"], booking["email"], booking["email"]),
        )
        return cur.rowcount > 0


def mark_arrived(booking_id: int) -> dict:
    """Registra l'arrivo e conta la visita una sola volta se il consenso è attivo."""
    with db(write=True) as c:
        booking = c.execute(
            "UPDATE bookings SET arrived_at=COALESCE(arrived_at, now()), updated_at=now() "
            "WHERE id=%s AND status='confirmed' AND booking_date <= %s "
            "RETURNING id, email, phone, arrived_at, marketing_visit_counted_at",
            (booking_id, now_local().strftime("%Y-%m-%d")),
        ).fetchone()
        if not booking:
            return {"ok": False, "error": "Prenotazione confermata non trovata o data futura."}

        contact = c.execute(
            "SELECT id, visite_totali FROM marketing_contacts WHERE revocato_il IS NULL "
            "AND scadenza_consenso > now() AND (phone=%s OR "
            "(%s <> '' AND email IS NOT NULL AND lower(email)=lower(%s))) "
            "ORDER BY (phone=%s) DESC LIMIT 1 FOR UPDATE",
            (booking["phone"], booking["email"], booking["email"], booking["phone"]),
        ).fetchone()

        if not contact or booking["marketing_visit_counted_at"]:
            return {"ok": True, "arrived_at": booking["arrived_at"], "visit_counted": False,
                    "visits": contact["visite_totali"] if contact else None}

        counted = c.execute(
            "UPDATE marketing_contacts SET visite_totali=visite_totali+1, ultima_visita=%s, "
            "updated_at=now() WHERE id=%s RETURNING visite_totali",
            (booking["arrived_at"], contact["id"]),
        ).fetchone()
        c.execute(
            "UPDATE bookings SET marketing_visit_counted_at=now() "
            "WHERE id=%s AND marketing_visit_counted_at IS NULL",
            (booking["id"],),
        )
        return {"ok": True, "arrived_at": booking["arrived_at"], "visit_counted": True,
                "visits": counted["visite_totali"]}



def admin_cancel(booking_id: int) -> bool:
    with db(write=True) as c:
        cur = c.execute(
            "UPDATE bookings SET status='cancelled' WHERE id=%s AND status='confirmed'", (booking_id,)
        )
        return cur.rowcount == 1
