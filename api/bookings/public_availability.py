"""Public, read-only availability for a whole evening (no table turnover)."""
import calendar
import re
from datetime import date, timedelta

from config import CLOSED_WEEKDAYS, MAX_ADVANCE_DAYS, MAX_PARTY_SIZE
from database import db
from .dates import now_local
from .tables import TABLES, _units
from .occupancy import reconstruct


def month_availability(month: str, party_size: int):
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Mese non valido.")
    if type(party_size) is not int or not 1 <= party_size <= MAX_PARTY_SIZE:
        raise ValueError(f"Online puoi verificare da 1 a {MAX_PARTY_SIZE} persone.")
    year, number = map(int, month.split("-"))
    first = date(year, number, 1)
    last = date(year, number, calendar.monthrange(year, number)[1])
    now = now_local()
    horizon = now.date() + timedelta(days=MAX_ADVANCE_DAYS)
    if last < now.date() or first > horizon:
        raise ValueError("Mese fuori dal periodo prenotabile.")
    with db() as connection:
        # First statement: enforce read-only at PostgreSQL transaction level.
        connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL statement_timeout = '5000ms'")
        rows = connection.execute(
            "SELECT id, booking_date, booking_time, party_size, tables FROM bookings "
            "WHERE booking_date >= %s AND booking_date <= %s AND status='confirmed'",
            (max(first, now.date()).isoformat(), min(last, horizon).isoformat()),
        ).fetchall()
        closures = connection.execute(
            "SELECT booking_date FROM public.online_booking_closures WHERE booking_date BETWEEN %s AND %s",
            (first, last),
        ).fetchall()
    closed_online = {str(row["booking_date"]) for row in closures}
    occupied, covers, uncertain = {}, {}, set()
    grouped = {}
    for row in rows:
        grouped.setdefault(str(row["booking_date"]), []).append(row)
    for day, bookings in grouped.items():
        snapshot, unresolved = reconstruct(bookings)
        if unresolved:
            uncertain.add(day)
        covers[day] = sum(row["party_size"] for row in bookings)
        occupied[day] = {t.strip() for row in snapshot.rows for t in (row["tables"] or "").split(",") if t.strip()}
    result = []
    for value in range(1, last.day + 1):
        day = date(year, number, value)
        key = day.isoformat()
        if day < now.date():
            status = "past"
        elif day > horizon:
            status = "outside_window"
        elif day.weekday() in CLOSED_WEEKDAYS or key in closed_online:
            status = "closed"
        elif key in uncertain:
            status = "unverified"
        elif covers.get(key, 0) + party_size > sum(TABLES.values()):
            status = "full"
        else:
            busy = occupied.get(key, set())
            status = "available" if any(seats >= party_size and not busy.intersection(ids) for ids, seats in _units()) else "full"
        result.append({"date": key, "status": status})
    return {"month": month, "party_size": party_size, "days": result}
