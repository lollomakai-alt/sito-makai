"""Disposizione, combinazioni e disponibilità dei tavoli."""
from datetime import datetime, timedelta

from config import STAY_MINUTES, MIN_ADVANCE_MINUTES
from .dates import now_local, _parse, _slots

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


def _units():
    """Tutte le sistemazioni possibili: singoli tavoli + combinazioni ammesse."""
    units = [([t], seats) for t, seats in TABLES.items()]
    units += [(list(ids), seats) for ids, seats in COMBINATIONS]
    return units



def _occupied_tables(c, dt: datetime, exclude_id=None) -> set:
    rows = c.execute(
        "SELECT id, booking_date, booking_time, party_size, tables FROM bookings "
        "WHERE booking_date=%s AND status='confirmed'",
        (dt.strftime("%Y-%m-%d"),),
    ).fetchall()
    if not getattr(c, "reconstructed_occupancy", False):
        from .occupancy import reconstruct, booking_datetime
        snapshot, unresolved = reconstruct([r for r in rows if r["id"] != exclude_id])
        for row in snapshot.rows:
            other = booking_datetime(row)
            if row["id"] in unresolved and (other is None or abs((other - dt).total_seconds()) < STAY_MINUTES * 60):
                return set(TABLES)
        rows = snapshot.rows
    busy = set()
    for r in rows:
        if exclude_id is not None and r["id"] == exclude_id:
            continue
        other = _parse(str(r["booking_date"]), str(r["booking_time"])[:5])
        if other and abs((other - dt).total_seconds()) < STAY_MINUTES * 60:
            busy.update(t.strip() for t in (r["tables"] or "").split(",") if t.strip())
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

