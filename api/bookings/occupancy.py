"""Deterministic in-memory reconstruction; never writes bookings."""
from config import STAY_MINUTES
from .dates import _parse


class Snapshot:
    reconstructed_occupancy = True

    def __init__(self, rows):
        self.rows = [dict(row) for row in rows]

    def execute(self, sql, params):
        self.matches = [row for row in self.rows if str(row['booking_date']) == params[0]]
        return self

    def fetchall(self):
        return self.matches


def booking_datetime(row):
    return _parse(str(row['booking_date']), str(row['booking_time'])[:5])


def valid_assignment(value, people):
    from .tables import _units
    ids = [t.strip() for t in (value or '').split(',') if t.strip()]
    return (type(people) is int and people >= 1 and bool(ids) and len(ids) == len(set(ids))
            and any(set(ids) == set(unit) and seats >= people for unit, seats in _units()))


def overlaps(left, right):
    a, b = booking_datetime(left), booking_datetime(right)
    return a is None or b is None or abs((a - b).total_seconds()) < STAY_MINUTES * 60


def reconstruct(rows):
    from .tables import _find_tables
    snapshot = Snapshot(rows)
    snapshot.rows.sort(key=lambda row: (str(row['booking_date']), str(row['booking_time']), row['id']))
    unresolved, pending = set(), []
    for row in snapshot.rows:
        if not booking_datetime(row) or type(row['party_size']) is not int or row['party_size'] < 1:
            unresolved.add(row['id'])
        elif not valid_assignment(row['tables'], row['party_size']):
            pending.append(row)
            row['tables'] = ''
        else:
            row['tables'] = ','.join(t.strip() for t in row['tables'].split(',') if t.strip())
    fixed = [r for r in snapshot.rows if r not in pending and r['id'] not in unresolved]
    for i, left in enumerate(fixed):
        for right in fixed[i + 1:]:
            if overlaps(left, right) and set(left['tables'].split(',')).intersection(right['tables'].split(',')):
                unresolved.update((left['id'], right['id']))
    for row in pending:
        assigned = _find_tables(snapshot, booking_datetime(row), row['party_size'], exclude_id=row['id'])
        if assigned:
            row['tables'] = ','.join(assigned)
        else:
            unresolved.add(row['id'])
    return snapshot, unresolved
