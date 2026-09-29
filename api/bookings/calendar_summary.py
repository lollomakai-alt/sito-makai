"""Riepilogo mensile dei soli coperti confermati."""
import calendar
import re

from database import db


def month_summary(month: str):
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Mese non valido.")
    year, number = map(int, month.split("-"))
    if year < 1:
        raise ValueError("Mese non valido.")
    last_day = calendar.monthrange(year, number)[1]
    with db() as connection:
        rows = connection.execute(
            "SELECT booking_date, SUM(party_size) AS covers, COUNT(*) AS booking_count "
            "FROM bookings WHERE booking_date >= %s AND booking_date <= %s "
            "AND status='confirmed' GROUP BY booking_date ORDER BY booking_date",
            (f"{month}-01", f"{month}-{last_day:02d}"),
        ).fetchall()
    return [
        {"date": str(row["booking_date"]), "covers": int(row["covers"]),
         "booking_count": int(row["booking_count"])}
        for row in rows
    ]
