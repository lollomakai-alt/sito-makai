"""Interfaccia pubblica compatibile con il precedente modulo bookings.py."""

from config import DATABASE_URL
from database import init_db
from .dates import now_local
from .validators import normalize_email, normalize_phone
from .service import (
    check_availability, create_booking, find_bookings, modify_booking,
    cancel_booking, list_day, admin_cancel,
)

__all__ = [
    "DATABASE_URL", "init_db", "now_local", "normalize_email", "normalize_phone",
    "check_availability", "create_booking", "find_bookings", "modify_booking",
    "cancel_booking", "list_day", "admin_cancel",
]
