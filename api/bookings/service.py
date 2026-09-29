"""Operazioni sulle prenotazioni e agenda del gestore."""
from config import MAX_ACTIVE_PER_PHONE
from database import db
from .dates import now_local, _parse
from .validators import normalize_email, normalize_phone, _validate
from .tables import _find_tables, _alternatives

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
                   party_size: int, notes: str = "", request_started_at=None) -> dict:
    """Salva solo dopo il sì al riepilogo; verifica limiti e tavoli nella transazione.

    request_started_at proviene dalla sessione firmata dal server: permette di
    riconoscere un reinvio della stessa conferma, anche su processi diversi.
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
    notes = (notes or "").strip()[:300]

    with db(write=True) as c:
        # Read under the same write lock as the insert. A lost HTTP response must
        # not create a second booking when the client retries its signed request.
        if request_started_at is not None:
            previous = c.execute(
                "SELECT id, name, booking_date, booking_time, party_size, status FROM bookings "
                "WHERE name=%s AND email=%s AND phone=%s AND booking_date=%s "
                "AND booking_time=%s AND party_size=%s AND notes=%s "
                "AND created_at >= to_timestamp(%s) ORDER BY id LIMIT 1",
                (name, p, ph, date, time, party_size, notes, request_started_at),
            ).fetchone()
            if previous:
                if previous["status"] != "confirmed":
                    return {"ok": False, "code": "cancelled", "error":
                            "Questa richiesta è stata annullata. Contatta il locale per riprenotare."}
                return {"ok": True, "booking_id": previous["id"], "name": previous["name"],
                        "date": previous["booking_date"], "time": previous["booking_time"],
                        "party_size": previous["party_size"]}
        dt, err = _validate(date, time, party_size)
        if err:
            return {"ok": False, "error": err}
        if len(_upcoming_for_phone(c, ph)) >= MAX_ACTIVE_PER_PHONE:
            return {"ok": False, "code": "phone_limit", "error":
                    f"Questo telefono ha già {MAX_ACTIVE_PER_PHONE} prenotazioni attive. Per altre chiamaci."}
        assigned = _find_tables(c, dt, party_size)
        if not assigned:
            return {"ok": False, "error": "Non c'è più posto a quell'orario.",
                    "alternative_times": _alternatives(c, dt, party_size)}
        cur = c.execute(
            "INSERT INTO bookings (name, email, phone, booking_date, booking_time, party_size, notes, "
            "tables, status, source, reminder_status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'confirmed','ai','skipped') RETURNING id",
            (name, p, ph, dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"), party_size,
             notes, ",".join(assigned)),
        )
        return {"ok": True, "booking_id": cur.fetchone()["id"], "name": name,
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
        if not assigned:
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
            "SELECT id, name, email, phone, tables, booking_date, booking_time, party_size, notes, status "
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

