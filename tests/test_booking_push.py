import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
import booking_push


class BookingPushTests(unittest.TestCase):
    def test_loads_committed_booking_and_calls_edge_with_minimal_server_payload(self):
        booking = {
            'id': 42,
            'source': 'booking',
            'status': 'confirmed',
            'name': 'Mario Rossi',
            'booking_date': '2026-10-08',
            'booking_time': '20:15:00',
            'party_size': 3,
        }
        calls = []

        class FakeServer:
            def request(self, method, path, payload=None):
                calls.append((method, path, payload))
                if method == 'GET':
                    return [booking]
                return {'queued': True, 'sent': 1, 'stale': 0, 'failed': 0}

        with patch('booking_push.SupabaseServer', return_value=FakeServer()):
            result = booking_push.send_new_online_booking_push(42)

        self.assertEqual(result['queued'], True)
        self.assertEqual(calls[0], (
            'GET',
            '/rest/v1/bookings?select=id,source,status,name,booking_date,booking_time,party_size&id=eq.42&limit=1',
            None,
        ))
        self.assertEqual(calls[1], (
            'POST',
            '/functions/v1/web-push-admin',
            {
                'action': 'new-online-booking',
                'booking': booking,
            },
        ))
        self.assertNotIn('phone', calls[1][2]['booking'])
        self.assertNotIn('email', calls[1][2]['booking'])

    def test_does_not_call_edge_for_missing_or_nonconfirmed_booking(self):
        class FakeServer:
            def request(self, method, path, payload=None):
                return []

        with patch('booking_push.SupabaseServer', return_value=FakeServer()):
            with self.assertRaises(RuntimeError):
                booking_push.send_new_online_booking_push(42)

        pending_calls = []

        class PendingServer:
            def request(self, method, path, payload=None):
                pending_calls.append((method, path))
                return [{
                    'id': 42, 'source': 'booking', 'status': 'pending',
                    'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                    'booking_time': '20:15', 'party_size': 3,
                }]

        with patch('booking_push.SupabaseServer', return_value=PendingServer()) as server:
            with self.assertRaises(RuntimeError):
                booking_push.send_new_online_booking_push(42)
        self.assertEqual(pending_calls, [(
            'GET',
            '/rest/v1/bookings?select=id,source,status,name,booking_date,booking_time,party_size&id=eq.42&limit=1',
        )])

    def test_surfaces_edge_function_errors_to_the_nonfatal_api_boundary(self):
        class FailingServer:
            def request(self, method, path, payload=None):
                if method == 'GET':
                    return [{
                        'id': 42, 'source': 'booking', 'status': 'confirmed',
                        'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                        'booking_time': '20:15', 'party_size': 3,
                    }]
                raise RuntimeError('private edge response')

        with patch('booking_push.SupabaseServer', return_value=FailingServer()):
            with self.assertRaisesRegex(RuntimeError, 'private edge response'):
                booking_push.send_new_online_booking_push(42)

    def test_rejects_malformed_edge_results_without_retrying(self):
        booking = [{
            'id': 42, 'source': 'booking', 'status': 'confirmed',
            'name': 'Mario Rossi', 'booking_date': '2026-10-08',
            'booking_time': '20:15', 'party_size': 3,
        }]
        invalid_results = [
            None,
            {'queued': False, 'sent': 0, 'failed': 0, 'stale': 0},
            {'queued': True, 'sent': 1, 'failed': 0},
            {'queued': True, 'sent': True, 'failed': 0, 'stale': 0},
            {'queued': True, 'sent': 0, 'failed': -1, 'stale': 0},
            {'queued': True, 'sent': 0, 'failed': 0, 'stale': '0'},
        ]
        for edge_result in invalid_results:
            requests = []

            class MalformedServer:
                def request(self, method, path, payload=None):
                    requests.append((method, path))
                    return booking if method == 'GET' else edge_result

            with self.subTest(edge_result=edge_result), \
                    patch('booking_push.SupabaseServer', return_value=MalformedServer()):
                with self.assertRaises(RuntimeError):
                    booking_push.send_new_online_booking_push(42)
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[-1][1], '/functions/v1/web-push-admin')

    def test_reports_partial_delivery_counts_without_retrying(self):
        requests = []

        class PartialServer:
            def request(self, method, path, payload=None):
                requests.append((method, path))
                if method == 'GET':
                    return [{
                        'id': 42, 'source': 'booking', 'status': 'confirmed',
                        'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                        'booking_time': '20:15', 'party_size': 3,
                    }]
                return {'queued': True, 'sent': 1, 'failed': 2, 'stale': 3}

        with patch('booking_push.SupabaseServer', return_value=PartialServer()), \
                self.assertLogs('makai', level='WARNING') as logs:
            result = booking_push.send_new_online_booking_push(42)

        self.assertEqual(result, {'queued': True, 'sent': 1, 'failed': 2, 'stale': 3})
        self.assertEqual(len(requests), 2)
        self.assertIn('sent=1 stale=3 failed=2', logs.output[0])

    def test_timeout_is_not_retried_after_the_edge_request_may_have_been_received(self):
        requests = []

        class TimeoutServer:
            def request(self, method, path, payload=None):
                requests.append((method, path))
                if method == 'GET':
                    return [{
                        'id': 42, 'source': 'booking', 'status': 'confirmed',
                        'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                        'booking_time': '20:15', 'party_size': 3,
                    }]
                raise TimeoutError('response lost after request')

        with patch('booking_push.SupabaseServer', return_value=TimeoutServer()):
            with self.assertRaisesRegex(TimeoutError, 'response lost'):
                booking_push.send_new_online_booking_push(42)

        self.assertEqual(requests.count(('POST', '/functions/v1/web-push-admin')), 1)


if __name__ == '__main__':
    unittest.main()
