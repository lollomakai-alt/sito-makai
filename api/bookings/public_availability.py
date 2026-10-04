"""Public, read-only availability for a whole evening (no table turnover)."""
import calendar
import re
from datetime import date, timedelta

from config import CLOSED_WEEKDAYS, MAX_ADVANCE_DAYS, MAX_PARTY_SIZE
from database import db
from .dates import now_local


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
            "SELECT to_char(calendar_day, 'YYYY-MM-DD') AS booking_date, "
            "private.online_day_status(to_char(calendar_day, 'YYYY-MM-DD'), %s, NULL) AS status "
            "FROM generate_series(%s::date, %s::date, interval '1 day') AS calendar_day",
            (party_size, max(first, now.date()).isoformat(), min(last, horizon).isoformat()),
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
    return {"month": month, "party_size": party_size, "days": result}
