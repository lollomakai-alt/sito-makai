"""Read-only availability from the canonical SQL planner, by service and slot."""
import calendar
import re
from datetime import date, timedelta

from config import CLOSED_WEEKDAYS, MAX_ADVANCE_DAYS, MAX_PARTY_SIZE
from database import db
from .dates import now_local


def month_availability(month: str, party_size: int, booking_type: str = "normale", booking_time = None):
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Mese non valido.")
    if type(party_size) is not int or not 1 <= party_size <= MAX_PARTY_SIZE:
        raise ValueError(f"Online puoi verificare da 1 a {MAX_PARTY_SIZE} persone.")
    if booking_type not in ("normale", "dopocena"):
        raise ValueError("Servizio non valido.")
    slots = ["22:30","23:00","23:30","00:00"] if booking_type == "dopocena" else ["19:00","19:30","20:00","20:30","21:00","21:30","22:00","22:30"]
    if booking_time and booking_time not in slots:
        raise ValueError("Orario non valido per il servizio.")
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
            "SELECT to_char(calendar_day, 'YYYY-MM-DD') AS booking_date, "
            "private.online_slot_status(to_char(calendar_day, 'YYYY-MM-DD'), %s, %s, %s, NULL) AS status "
            "FROM generate_series(%s::date, %s::date, interval '1 day') AS calendar_day",
            (booking_time or slots[0], party_size, booking_type, max(first, now.date()).isoformat(), min(last, horizon).isoformat()),
        ).fetchall()
    statuses = {str(row['booking_date']): row['status'] for row in rows}
    result = []
    for value in range(1, last.day + 1):
        day = date(year, number, value)
        key = day.isoformat()
        if day < now.date():
            status = "past"
        elif day > horizon:
            status = "outside_window"
        elif day.weekday() in CLOSED_WEEKDAYS:
            status = "closed"
        else:
            status = statuses.get(key, "unverified")
        result.append({"date": key, "status": status})
    return {"month": month, "party_size": party_size, "days": result, "booking_type": booking_type, "booking_time": booking_time}
