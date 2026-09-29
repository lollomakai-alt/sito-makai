"""Date e orari condivisi dalle prenotazioni."""
from datetime import datetime, timedelta

from config import TZ, SLOT_START, SLOT_END, SLOT_MINUTES

def now_local() -> datetime:
    return datetime.now(TZ)



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

