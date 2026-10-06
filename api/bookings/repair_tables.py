"""Explicit report/apply workflow for legacy bookings; never run on startup."""
import hashlib
import json
from datetime import datetime

from database import db
from .dates import now_local, _parse
from .tables import TABLES, JOINABLE_ROWS, MAX_COMBO_SEATS, _find_tables
from .occupancy import Snapshot, reconstruct


def make_report(rows, cutoff):
    snapshot = Snapshot(rows)
    ordered = sorted(snapshot.rows, key=lambda row: (str(row['booking_date']), str(row['booking_time']), row['id']))
    fingerprint = json.dumps({'rows': ordered, 'tables': TABLES, 'joinable': JOINABLE_ROWS,
                              'max_combo': MAX_COMBO_SEATS, 'occupancy_policy': 'explicit-release-by-booking-day-v1'}, sort_keys=True, default=str)
    report = {'version': 1, 'cutoff': cutoff.isoformat(),
              'snapshot_sha256': hashlib.sha256(fingerprint.encode()).hexdigest(), 'bookings': []}
    resolved, unresolved = reconstruct(rows)
    by_id = {row['id']: row for row in resolved.rows}
    for row in ordered:
        if row.get('status', 'confirmed') != 'confirmed' or row['party_size'] < 1 or (row['tables'] or '').strip():
            continue
        dt = _parse(str(row['booking_date']), str(row['booking_time'])[:5])
        if dt and dt < cutoff:
            continue
        assigned = by_id[row['id']]['tables'].split(',') if dt and row['id'] not in unresolved else None
        report['bookings'].append({'id': row['id'], 'name': row['name'],
            'date': str(row['booking_date']), 'time': str(row['booking_time']),
            'party_size': row['party_size'], 'proposed_tables': assigned or [],
            'result': 'ASSEGNABILE' if assigned else 'TAVOLO DA ASSEGNARE'})
        if assigned:
            row['tables'] = ','.join(assigned)
    report['involved'] = len(report['bookings'])
    report['assignable'] = sum(bool(row['proposed_tables']) for row in report['bookings'])
    report['unassigned'] = report['involved'] - report['assignable']
    return report


def read_rows(connection, cutoff):
    return connection.execute(
        "SELECT id, name, booking_date, booking_time, party_size, tables, status FROM bookings "
        "WHERE status NOT IN ('cancelled','no_show') AND booking_date >= %s "
        "ORDER BY booking_date, booking_time, id", (cutoff.date().isoformat(),)
    ).fetchall()


def dry_run():
    cutoff = now_local()
    with db() as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        connection.execute("SET LOCAL statement_timeout = '10000ms'")
        return make_report(read_rows(connection, cutoff), cutoff)


def apply_report(approved):
    cutoff = datetime.fromisoformat(approved['cutoff'])
    if cutoff.tzinfo is None:
        raise ValueError('Report non valido.')
    with db(write=True) as connection:
        connection.execute("SET LOCAL lock_timeout = '5000ms'")
        # Also protects against writes from other applications not using our advisory lock.
        connection.execute('LOCK TABLE bookings IN SHARE ROW EXCLUSIVE MODE')
        current = make_report(read_rows(connection, cutoff), cutoff)
        if current != approved:
            raise ValueError('Agenda o configurazione cambiata: genera e approva un nuovo DRY RUN.')
        now = now_local()
        if any((_parse(row['date'], row['time'][:5]) or cutoff) < now for row in current['bookings'] if row['proposed_tables']):
            raise ValueError('Una prenotazione non è più futura: genera un nuovo DRY RUN.')
        changed = []
        for row in current['bookings']:
            if not row['proposed_tables']:
                continue
            fresh, unresolved = reconstruct(read_rows(connection, cutoff))
            assigned_row = next(r for r in fresh.rows if r['id'] == row['id'])
            assigned = assigned_row['tables'].split(',') if row['id'] not in unresolved else None
            if assigned != row['proposed_tables']:
                raise ValueError('Assegnazione cambiata: operazione annullata.')
            result = connection.execute(
                "UPDATE bookings SET tables=%s WHERE id=%s AND status='confirmed' "
                "AND (tables IS NULL OR btrim(tables)='')",
                (','.join(assigned), row['id']),
            )
            if result.rowcount != 1:
                raise ValueError('Prenotazione cambiata: operazione annullata.')
            changed.append(row['id'])
    return changed
