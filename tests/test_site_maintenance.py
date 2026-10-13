import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from fastapi.testclient import TestClient
import index
import maintenance_mode
from bookings.online import create_online_booking


class FakeConnection:
    def __init__(self, active=False, missing=False):
        self.active = active
        self.missing = missing
        self.calls = []
        self.last = ''

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self.last = sql
        if self.missing and 'site_maintenance' in sql:
            raise RuntimeError('private database detail')
        if 'UPDATE private.site_maintenance SET' in sql:
            self.active = params[0]
        return self

    def fetchone(self):
        if 'FROM private.site_maintenance WHERE' in self.last:
            return {'active': self.active}
        return None

    def fetchall(self):
        return []


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(index.app)
        index._hits.clear()

    def fake_db(self, connection):
        @contextmanager
        def database(write=False):
            yield connection
        return database

    def test_public_status_active_inactive_and_error_fail_closed(self):
        for active in (False, True):
            connection = FakeConnection(active=active)
            with patch('maintenance_mode.db', self.fake_db(connection)):
                response = self.client.get('/api/site-maintenance')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'active': active})
            self.assertEqual(response.headers['cache-control'], 'no-store')
        with patch('maintenance_mode.db', self.fake_db(FakeConnection(missing=True))):
            response = self.client.get('/api/site-maintenance')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('database detail', response.text)

    def test_online_booking_blocked_before_receipt_or_insert_and_on_error(self):
        body = ('Mario Rossi', '3331234567', '2026-10-06', '20:00', 2,
                '11111111-1111-4111-8111-111111111111')
        for connection, error in ((FakeConnection(active=True), maintenance_mode.MaintenanceActive),
                                  (FakeConnection(missing=True), RuntimeError)):
            with patch('bookings.online.db', self.fake_db(connection)):
                with self.assertRaises(error):
                    create_online_booking(*body, privacy=True)
            self.assertFalse(any('INSERT' in sql or 'online_booking_receipts' in sql
                                 for sql, _ in connection.calls))
        with patch('index.create_online_booking', side_effect=maintenance_mode.MaintenanceActive):
            response = self.client.post('/api/bookings', json={
                'name': body[0], 'phone': body[1], 'date': body[2], 'time': body[3],
                'party_size': body[4], 'request_id': body[5], 'privacy': True,
            })
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['retry-after'], '300')

    def test_public_availability_does_not_claim_open_slots_during_maintenance(self):
        with patch('index.public_status', return_value={'active': True}), \
                patch('index.month_availability') as availability:
            response = self.client.get('/api/booking-availability?month=2026-10&party_size=2')
        self.assertEqual(response.status_code, 503)
        availability.assert_not_called()

    def test_admin_only_toggle_persists_audit_and_preserves_bookings(self):
        connection = FakeConnection()
        with patch('maintenance_mode.require_admin', return_value={'username': 'admin-id'}) as admin, \
                patch('maintenance_mode.require_browser_action') as browser, \
                patch('maintenance_mode.db', self.fake_db(connection)):
            result = maintenance_mode.change_status(maintenance_mode.MaintenanceChange(active=True), object())
            self.assertEqual(result, {'active': True})
            self.assertTrue(connection.active)
            self.assertEqual(sum('site_maintenance_history' in sql for sql, _ in connection.calls), 1)
            self.assertFalse(any('public.bookings' in sql for sql, _ in connection.calls))
            maintenance_mode.change_status(maintenance_mode.MaintenanceChange(active=True), object())
            self.assertEqual(sum('site_maintenance_history' in sql for sql, _ in connection.calls), 1)
            maintenance_mode.change_status(maintenance_mode.MaintenanceChange(active=False), object())
            self.assertFalse(connection.active)
            self.assertEqual(sum('site_maintenance_history' in sql for sql, _ in connection.calls), 2)
            self.assertEqual(admin.call_args.kwargs['allowed_roles'], ('admin',))
            self.assertEqual(browser.call_count, 3)

    def test_admin_routes_reject_unauthorized_access_before_database(self):
        with patch('maintenance_mode.db') as database:
            self.assertIn(self.client.get('/api/admin/site-maintenance').status_code, (403, 503))
            self.assertIn(self.client.post('/api/admin/site-maintenance', json={'active': True}).status_code, (403, 503))
            database.assert_not_called()


if __name__ == '__main__':
    unittest.main()
