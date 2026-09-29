"""Pulizia periodica delle prenotazioni scadute."""
import asyncio
import logging
from datetime import timedelta

from config import RETENTION_DAYS
from database import db
from .dates import now_local

logger = logging.getLogger("makai")


def purge_old_bookings() -> int:
    limit = (now_local() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    with db(write=True) as c:
        return c.execute("DELETE FROM bookings WHERE booking_date < %s", (limit,)).rowcount


async def cleanup_loop():
    while True:
        try:
            count = await asyncio.to_thread(purge_old_bookings)
            if count:
                logger.info("Eliminate %s prenotazioni vecchie", count)
        except Exception:
            logger.exception("Errore nella pulizia delle prenotazioni")
        await asyncio.sleep(3600)
