import sys
import unittest
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from bookings.occupancy import Snapshot, reconstruct, valid_assignment, booking_datetime
from bookings.tables import _find_tables, TABLES
from bookings.service import create_booking
from test_repair_tables import row, NOW

class LiveLikeConnection(Snapshot):
    reconstructed_occupancy = False

class OccupancyTests(unittest.TestCase):
    def test_missing_table_is_reconstructed_using_actual_finder(self):
        rows = [row(1, tables=None), row(2, tables='')]
        resolved, errors = reconstruct(rows)
        self.assertFalse(errors)
        self.assertEqual([r['tables'] for r in resolved.rows], ['12', '13'])
        self.assertIsNone(rows[0]['tables'])
        self.assertEqual(_find_tables(LiveLikeConnection(rows), booking_datetime(rows[0]), 2), ['14'])

    def test_overlapping_unknown_large_group_blocks_new_bookings(self):
        rows = [row(1, people=30)]
        self.assertIsNone(_find_tables(LiveLikeConnection(rows), booking_datetime(row(2)), 2))

    def test_assigned_tables_never_reuse_after_elapsed_time(self):
        rows = [row(int(t), tables=t, people=n) for t, n in TABLES.items()]
        conn = LiveLikeConnection(rows)
        self.assertIsNone(_find_tables(conn, booking_datetime(row(100, '21:59')), 2))
        self.assertIsNone(_find_tables(conn, booking_datetime(row(100, '22:00')), 2))
        self.assertIsNone(_find_tables(conn, booking_datetime(row(100, '23:59')), 2))

    def test_explicit_release_statuses_and_completed_assignment(self):
        for status in ('confirmed', 'arrived', 'completed'):
            rows = [dict(row(int(t), tables=t, people=n), status=status) for t, n in TABLES.items()]
            self.assertIsNone(_find_tables(LiveLikeConnection(rows), booking_datetime(row(100, '23:59')), 2))
            self.assertTrue(all(r['status'] == status for r in rows))
        cleared = [dict(row(i, tables=''), status='completed') for i in (1, 2)]
        self.assertEqual(_find_tables(LiveLikeConnection(cleared), booking_datetime(row(100)), 2), ['12'])
        self.assertEqual(cleared[0]['tables'], '')
        for status in ('cancelled', 'no_show'):
            rows = [dict(row(int(t), tables=t, people=n), status=status) for t, n in TABLES.items()]
            self.assertEqual(_find_tables(LiveLikeConnection(rows), booking_datetime(row(100)), 2), ['12'])

    def test_existing_double_assignment_is_conservative(self):
        rows = [row(1, tables='12'), row(2, tables='12')]
        self.assertIsNone(_find_tables(LiveLikeConnection(rows), booking_datetime(row(3)), 2))

    def test_disallowed_combinations_are_never_valid(self):
        for value, size in [('12,14', 4), ('12,12', 4), ('999', 1), ('', 1), ('12', 3)]:
            self.assertFalse(valid_assignment(value, size))
        self.assertTrue(valid_assignment('10,11', 6))

    def test_online_rejects_empty_duplicate_or_disallowed_assignments(self):
        class Connection:
            def execute(self, sql, *args):
                if 'online_booking_closures' in sql:
                    return self
                raise AssertionError('No INSERT is allowed')
            def fetchone(self):
                return None
        @contextmanager
        def connection(**kwargs):
            yield Connection()
        with patch('bookings.service.db', connection), patch('bookings.service._validate', return_value=(NOW,None)), patch('bookings.service._upcoming_for_phone', return_value=[]), patch('bookings.service._alternatives', return_value=[]):
            for assignment in (None, [], ['12','12'], ['12','14'], ['999'], ['12']):
                with self.subTest(assignment=assignment), patch('bookings.service._find_tables', return_value=assignment):
                    self.assertFalse(create_booking('Test Name','test@example.com','+393331234567','2026-10-04','20:00',4)['ok'])

    def test_online_write_with_legacy_occupancy_never_overbooks(self):
        class Connection(LiveLikeConnection):
            def execute(self, sql, params=None):
                self.last_sql = sql
                if 'online_booking_closures' in sql:
                    return self
                if sql.startswith('INSERT'):
                    self.saved = params
                    self.rows.append(row(100, tables=params[7], people=params[5]))
                    return self
                return super().execute(sql, params)
            def fetchone(self):
                return None if 'online_booking_closures' in self.last_sql else {'id':100}
        conn = Connection([row(int(t), tables=t, people=n) for t,n in TABLES.items() if t not in {'12','13'}] + [row(99, tables=None)])
        @contextmanager
        def connection(**kwargs):
            self.assertTrue(kwargs['write'])
            yield conn
        with patch('bookings.service.db', connection), patch('bookings.service._validate', return_value=(booking_datetime(row(1)),None)), patch('bookings.service._upcoming_for_phone', return_value=[]), patch('bookings.service._alternatives', return_value=[]):
            values = ('Test Name','test@example.com','+393331234567','2026-10-04','20:00',2)
            first = create_booking(*values)
            self.assertTrue(first['ok'])
            self.assertEqual(conn.saved[7], '13')
            self.assertTrue(valid_assignment(conn.saved[7],2))
            second = create_booking(*values)
            self.assertFalse(second['ok'])
        self.assertEqual(len([r for r in conn.rows if r['id']==100]),1)
        self.assertIsNone(next(r for r in conn.rows if r['id']==99)['tables'])

if __name__ == '__main__':
    unittest.main()
