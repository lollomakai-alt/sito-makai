import sys
import unittest
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from config import TZ
from bookings.public_availability import month_availability
from bookings.tables import TABLES


def booking(id=1, tables='', people=2, day='2026-10-06', time='20:00'):
    return dict(id=id, booking_date=day, booking_time=time, party_size=people, tables=tables)


def filled_tables(except_ids=(), day='2026-10-06'):
    return [booking(int(t), t, seats, day) for t, seats in TABLES.items() if t not in except_ids]


class AvailabilityTests(unittest.TestCase):
    def run_calendar(self, people, rows=(), now=None):
        statements = []
        class Connection:
            def execute(self, sql, args=None):
                statements.append((sql, args))
                return self
            def fetchall(self):
                return list(rows)
        @contextmanager
        def read_db():
            yield Connection()
        with patch('bookings.public_availability.db', read_db), patch('bookings.public_availability.now_local', return_value=now or datetime(2026, 10, 3, 12, tzinfo=TZ)):
            result = month_availability('2026-10', people)
        self.assertEqual(statements[0][0], 'SET TRANSACTION READ ONLY')
        self.assertEqual(len(statements), 3)
        self.assertIn("status='confirmed'", statements[2][0])
        self.assertNotIn('name', statements[2][0])
        return {day['date']: day['status'] for day in result['days']}

    def test_size_changes_availability_with_same_agenda(self):
        busy = [t for t in TABLES if t != '12']
        rows = filled_tables({'12'})
        self.assertEqual(self.run_calendar(2, rows)['2026-10-06'], 'available')
        self.assertEqual(self.run_calendar(3, rows)['2026-10-06'], 'full')

    def test_six_requires_suitable_joinable_tables(self):
        free = {'12', '14', '22'}
        rows = filled_tables(free)
        self.assertEqual(self.run_calendar(6, rows)['2026-10-06'], 'full')
        self.assertEqual(self.run_calendar(6)['2026-10-06'], 'available')

    def test_closed_past_and_unknown_table_data(self):
        rows = [booking(tables='unknown', people=30)]
        days = self.run_calendar(2, rows)
        self.assertEqual(days['2026-10-05'], 'closed')
        self.assertEqual(days['2026-10-02'], 'past')
        self.assertEqual(days['2026-10-06'], 'unverified')

    def test_empty_table_assignment_uses_known_cover_count(self):
        rows = [booking()]
        self.assertEqual(self.run_calendar(2, rows)['2026-10-06'], 'available')

        over_capacity = filled_tables()
        self.assertEqual(self.run_calendar(1, over_capacity)['2026-10-06'], 'full')

    def test_multiple_missing_assignments_count_against_remaining_tables(self):
        rows = filled_tables({'12', '13'}) + [booking(100, None), booking(101, '')]
        self.assertEqual(self.run_calendar(1, rows)['2026-10-06'], 'full')
        self.assertIsNone(rows[-2]['tables'])
        self.assertEqual(rows[-1]['tables'], '')

    def test_invalid_combination_is_reconstructed_in_memory(self):
        rows = [booking(tables='12,14', people=4)]
        self.assertEqual(self.run_calendar(6, rows)['2026-10-06'], 'available')
        self.assertEqual(rows[0]['tables'], '12,14')

    def test_october_28_29_30_regression(self):
        rows = [booking(83, '', 3, '2026-10-28'), booking(40, '', 4, '2026-10-29'),
                booking(63, '', 6, '2026-10-30'), booking(52, '', 30, '2026-10-30', '22:30')]
        for size in range(1, 7):
            days = self.run_calendar(size, rows)
            self.assertEqual(days['2026-10-28'], 'available')
            self.assertEqual(days['2026-10-29'], 'available')
            self.assertEqual(days['2026-10-30'], 'unverified')

    def test_today_available_even_late_in_the_evening(self):
        days = self.run_calendar(2, now=datetime(2026, 10, 3, 23, 59, tzinfo=TZ))
        self.assertEqual(days['2026-10-03'], 'available')
        self.assertEqual(days['2026-10-02'], 'past')

    def test_today_still_respects_capacity_and_closure(self):
        rows = filled_tables(day='2026-10-03')
        self.assertEqual(self.run_calendar(2, rows, now=datetime(2026, 10, 3, 23, 59, tzinfo=TZ))['2026-10-03'], 'full')
        self.assertEqual(self.run_calendar(2, now=datetime(2026, 10, 5, 12, tzinfo=TZ))['2026-10-05'], 'closed')

    def test_invalid_request_never_reads_database(self):
        with patch('bookings.public_availability.db') as db:
            for month, size in [('2026-10', 7), ('2026-10', 0), ('2026-10', True), ('2026-13', 2), ('2026-10', 2.5), ('0000-01', 2)]:
                with self.assertRaises(ValueError):
                    month_availability(month, size)
            db.assert_not_called()

    def test_database_failure_is_not_available(self):
        with patch('bookings.public_availability.now_local', return_value=datetime(2026, 10, 3, 12, tzinfo=TZ)), patch('bookings.public_availability.db', side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError):
                month_availability('2026-10', 2)

if __name__ == '__main__':
    unittest.main()
