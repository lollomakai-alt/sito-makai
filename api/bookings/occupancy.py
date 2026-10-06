"""Deterministic in-memory reconstruction; never writes bookings."""
from .dates import _parse


class Snapshot:
    reconstructed_occupancy = True

    def __init__(self, rows):
        self.rows = [dict(row) for row in rows if row.get('status') not in ('cancelled', 'no_show')]

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
    # Occupancy is scoped to the booked service day, never a timed stay.
    a, b = str(left.get('booking_date') or ''), str(right.get('booking_date') or '')
    return not a or not b or a == b


def reconstruct(rows):
    from .tables import _find_tables
    snapshot = Snapshot(rows)
    snapshot.rows.sort(key=lambda row: (str(row['booking_date']), str(row['booking_time']), row['id']))
    unresolved, pending = set(), []
    for row in snapshot.rows:
        if not booking_datetime(row) or type(row['party_size']) is not int or row['party_size'] < 1:
            unresolved.add(row['id'])
        elif row.get('status', 'confirmed') != 'confirmed' and not (row['tables'] or '').strip():
            # Explicitly cleared assignments are not reconstructed for seated/finished guests.
            continue
        elif not valid_assignment(row['tables'], row['party_size']):
            pending.append(row)
            row['tables'] = ''
        else:
            row['tables'] = ','.join(t.strip() for t in row['tables'].split(',') if t.strip())
    fixed = [r for r in snapshot.rows if r not in pending and r['id'] not in unresolved
             and (r['tables'] or '').strip()]
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
