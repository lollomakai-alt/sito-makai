import sys
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from contextlib import contextmanager
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from config import TZ
from bookings.repair_tables import make_report, apply_report
from bookings.tables import TABLES
from bookings.service import create_booking

NOW = datetime(2026, 10, 3, 12, tzinfo=TZ)
def row(id, time='20:00', tables=None, people=2):
    return dict(id=id, name='Test Name', booking_date='2026-10-04', booking_time=time, tables=tables, party_size=people)

class RepairTests(unittest.TestCase):
    def test_chronological_deterministic_and_no_overlap(self):
        rows = [row(3), row(2), row(1, tables='12')]
        report = make_report(rows, NOW)
        self.assertEqual([r['id'] for r in report['bookings']], [2, 3])
        assignments = [r['proposed_tables'] for r in report['bookings']]
        self.assertEqual(assignments, [['13'], ['14']])
        self.assertEqual(report, make_report(rows, NOW))
        self.assertIsNone(rows[0]['tables'])
        for entry in report['bookings']:
            next(r for r in rows if r['id'] == entry['id'])['tables'] = ','.join(entry['proposed_tables'])
        self.assertEqual(make_report(rows, NOW)['involved'], 0)

    def test_later_existing_booking_is_respected_without_turnover(self):
        report = make_report([row(1, tables=None), row(2, '21:00', '12'), row(3, '22:00')], NOW)
        self.assertEqual(report['bookings'][0]['proposed_tables'], ['13'])
        self.assertEqual(report['bookings'][1]['proposed_tables'], ['14'])

    def test_no_combination_leaves_original_empty(self):
        report = make_report([row(1, people=9)], NOW)
        self.assertEqual(report['unassigned'], 1)
        self.assertEqual(report['bookings'][0]['result'], 'TAVOLO DA ASSEGNARE')

    def test_all_tables_occupied_returns_unresolved(self):
        report = make_report([row(int(t), tables=t, people=seats) for t, seats in TABLES.items()] + [row(100)], NOW)
        self.assertEqual(report['unassigned'], 1)

    def test_changed_report_aborts_before_update(self):
        report = make_report([row(1)], NOW)
        report['bookings'][0]['proposed_tables'] = ['20']
        class Connection:
            def execute(self, sql, args=None):
                assert not sql.startswith('UPDATE')
        @contextmanager
        def connection(**kwargs):
            yield Connection()
        with patch('bookings.repair_tables.db', connection), patch('bookings.repair_tables.read_rows', return_value=[row(1)]):
            with self.assertRaises(ValueError):
                apply_report(report)

    def test_apply_matches_report_and_second_run_cannot_reassign(self):
        from bookings.repair_tables import Snapshot
        rows = [row(1), row(2)]
        report = make_report(rows, NOW)
        class Connection(Snapshot):
            def execute(self, sql, params=None):
                if sql.startswith('UPDATE'):
                    target = next(r for r in self.rows if r['id'] == params[1])
                    target['tables'] = params[0]
                    self.rowcount = 1
                    return self
                if sql.startswith('SELECT'):
                    return super().execute(sql, params)
                return self
        conn = Connection(rows)
        @contextmanager
        def connection(**kwargs):
            yield conn
        with patch('bookings.repair_tables.db', connection), patch('bookings.repair_tables.read_rows', side_effect=lambda *_: conn.rows), patch('bookings.repair_tables.now_local', return_value=NOW):
            self.assertEqual(apply_report(report), [1, 2])
            saved = [r['tables'] for r in conn.rows]
            with self.assertRaises(ValueError):
                apply_report(report)
            self.assertEqual([r['tables'] for r in conn.rows], saved)
            self.assertEqual(make_report(conn.rows, NOW)['involved'], 0)

    def test_online_insert_never_runs_without_assignment(self):
        class Connection:
            def execute(self, sql, *args):
                if 'online_booking_closures' in sql:
                    return self
                raise AssertionError('Unexpected SQL write')
            def fetchone(self):
                return None
        @contextmanager
        def connection(**kwargs):
            yield Connection()
        with patch('bookings.service.db', connection), patch('bookings.service._validate', return_value=(NOW, None)), patch('bookings.service._upcoming_for_phone', return_value=[]), patch('bookings.service._find_tables', return_value=None), patch('bookings.service._alternatives', return_value=[]):
            result = create_booking('Test Name', 'test@example.com', '+393331234567', '2026-10-04', '20:00', 2)
        self.assertFalse(result['ok'])

if __name__ == '__main__':
    unittest.main()
