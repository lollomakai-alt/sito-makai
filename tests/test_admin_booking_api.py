import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from fastapi.testclient import TestClient
import index


class SqlFailure(Exception):
    sqlstate = '23505'


class AdminBookingApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(index.app)
        self.body = {
            'name': 'Mario Rossi',
            'phone': '+393331234567',
            'date': '2026-10-10',
            'time': '20:00',
            'party_size': 2,
        }

    def _post_with_error(self, error):
        with (
            patch('index.require_agenda_gateway'),
            patch('index.require_browser_action'),
            patch('index.require_admin'),
            patch('index.bookings.create_admin_booking', side_effect=error),
            self.assertLogs('makai', level='WARNING') as logs,
        ):
            response = self.client.post('/api/admin/bookings', json=self.body)
        return response, '\n'.join(logs.output)

    def test_database_failure_logs_safe_category_and_sqlstate_only(self):
        error = SqlFailure(
            'INSERT failed for Mario Rossi +393331234567 using secret credentials'
        )
        response, logged = self._post_with_error(error)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {'detail': 'Prenotazione non salvata: controlla il database.'},
        )
        self.assertIn('category=SqlFailure', logged)
        self.assertIn('sqlstate=23505', logged)
        for sensitive in ('Mario Rossi', '+393331234567', 'secret credentials', 'INSERT failed'):
            self.assertNotIn(sensitive, response.text)
            self.assertNotIn(sensitive, logged)

    def test_non_database_failure_logs_category_and_marks_sqlstate_unavailable(self):
        response, logged = self._post_with_error(RuntimeError('private failure detail'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {'detail': 'Prenotazione non salvata: controlla il database.'},
        )
        self.assertIn('category=RuntimeError', logged)
        self.assertIn('sqlstate=unavailable', logged)
        self.assertNotIn('private failure detail', response.text)
        self.assertNotIn('private failure detail', logged)


if __name__ == '__main__':
    unittest.main()
