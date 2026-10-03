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
        rows = [{'booking_date': '2026-10-06', 'party_size': 40, 'tables': ','.join(busy)}]
        self.assertEqual(self.run_calendar(2, rows)['2026-10-06'], 'available')
        self.assertEqual(self.run_calendar(3, rows)['2026-10-06'], 'full')

    def test_six_requires_suitable_joinable_tables(self):
        free = {'12', '14', '22'}
        rows = [{'booking_date': '2026-10-06', 'party_size': 36, 'tables': ','.join(set(TABLES) - free)}]
        self.assertEqual(self.run_calendar(6, rows)['2026-10-06'], 'full')
        self.assertEqual(self.run_calendar(6)['2026-10-06'], 'available')

    def test_closed_past_and_unknown_table_data(self):
        rows = [{'booking_date': '2026-10-06', 'party_size': 2, 'tables': ''}]
        days = self.run_calendar(2, rows)
        self.assertEqual(days['2026-10-05'], 'closed')
        self.assertEqual(days['2026-10-02'], 'past')
        self.assertEqual(days['2026-10-06'], 'unverified')

    def test_today_available_even_late_in_the_evening(self):
        days = self.run_calendar(2, now=datetime(2026, 10, 3, 23, 59, tzinfo=TZ))
        self.assertEqual(days['2026-10-03'], 'available')
        self.assertEqual(days['2026-10-02'], 'past')

    def test_today_still_respects_capacity_and_closure(self):
        rows = [{'booking_date': '2026-10-03', 'party_size': 42, 'tables': ','.join(TABLES)}]
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
