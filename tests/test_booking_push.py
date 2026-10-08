import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
import booking_push


class BookingPushTests(unittest.TestCase):
    def test_edge_request_uses_push_secret_not_service_role_for_authorization(self):
        outbound = []

        class FakeResponse(BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class FakeOpener:
            def open(self, request, timeout):
                outbound.append(request)
                return FakeResponse(b'{}')

        with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://example.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'test-service-role',
        }), patch('supabase_server.build_opener', return_value=FakeOpener()):
            server = booking_push.SupabaseServer()
            server.request('GET', '/rest/v1/bookings')
            server.request('POST', '/functions/v1/web-push-admin', {},
                           authorization_key='test-push-secret', api_key='test-publishable')

        self.assertEqual(outbound[0].get_header('Authorization'), 'Bearer test-service-role')
        self.assertEqual(outbound[0].get_header('Apikey'), 'test-service-role')
        self.assertEqual(outbound[1].get_header('Authorization'), 'Bearer test-push-secret')
        self.assertEqual(outbound[1].get_header('Apikey'), 'test-publishable')

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
            def request(self, method, path, payload=None, **kwargs):
                calls.append((method, path, payload, kwargs))
                if method == 'GET':
                    return [booking]
                return {'queued': True, 'sent': 1, 'stale': 0, 'failed': 0}

        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': 'push-server-secret',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer', return_value=FakeServer()):
            result = booking_push.send_new_online_booking_push(42)

        self.assertEqual(result['queued'], True)
        self.assertEqual(calls[0][:3], (
            'GET',
            '/rest/v1/bookings?select=id,source,status,name,booking_date,booking_time,party_size&id=eq.42&limit=1',
            None,
        ))
        self.assertEqual(calls[0][3], {})
        self.assertEqual(calls[1][:3], (
            'POST',
            '/functions/v1/web-push-admin',
            {
                'action': 'new-online-booking',
                'booking': booking,
            },
        ))
        self.assertEqual(calls[1][3], {
            'authorization_key': 'push-server-secret',
            'api_key': 'publishable-key',
        })
        self.assertNotIn('phone', calls[1][2]['booking'])
        self.assertNotIn('email', calls[1][2]['booking'])

    def test_does_not_call_edge_for_missing_or_nonconfirmed_booking(self):
        class FakeServer:
            def request(self, method, path, payload=None, **kwargs):
                return []

        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': 'push-server-secret',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer', return_value=FakeServer()):
            with self.assertRaises(RuntimeError):
                booking_push.send_new_online_booking_push(42)

        pending_calls = []

        class PendingServer:
            def request(self, method, path, payload=None, **kwargs):
                pending_calls.append((method, path))
                return [{
                    'id': 42, 'source': 'booking', 'status': 'pending',
                    'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                    'booking_time': '20:15', 'party_size': 3,
                }]

        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': 'push-server-secret',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer', return_value=PendingServer()) as server:
            with self.assertRaises(RuntimeError):
                booking_push.send_new_online_booking_push(42)
        self.assertEqual(pending_calls, [(
            'GET',
            '/rest/v1/bookings?select=id,source,status,name,booking_date,booking_time,party_size&id=eq.42&limit=1',
        )])

    def test_surfaces_edge_function_errors_to_the_nonfatal_api_boundary(self):
        class FailingServer:
            def request(self, method, path, payload=None, **kwargs):
                if method == 'GET':
                    return [{
                        'id': 42, 'source': 'booking', 'status': 'confirmed',
                        'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                        'booking_time': '20:15', 'party_size': 3,
                    }]
                raise RuntimeError('private edge response')

        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': 'push-server-secret',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer', return_value=FailingServer()):
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
                def request(self, method, path, payload=None, **kwargs):
                    requests.append((method, path))
                    return booking if method == 'GET' else edge_result

            with self.subTest(edge_result=edge_result), \
                    patch.dict('os.environ', {
                        'MAKAI_PUSH_SECRET': 'push-server-secret',
                        'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
                    }), \
                    patch('booking_push.SupabaseServer', return_value=MalformedServer()):
                with self.assertRaises(RuntimeError):
                    booking_push.send_new_online_booking_push(42)
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[-1][1], '/functions/v1/web-push-admin')

    def test_reports_partial_delivery_counts_without_retrying(self):
        requests = []

        class PartialServer:
            def request(self, method, path, payload=None, **kwargs):
                requests.append((method, path))
                if method == 'GET':
                    return [{
                        'id': 42, 'source': 'booking', 'status': 'confirmed',
                        'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                        'booking_time': '20:15', 'party_size': 3,
                    }]
                return {'queued': True, 'sent': 1, 'failed': 2, 'stale': 3}

        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': 'push-server-secret',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer', return_value=PartialServer()), \
                self.assertLogs('makai', level='WARNING') as logs:
            result = booking_push.send_new_online_booking_push(42)

        self.assertEqual(result, {'queued': True, 'sent': 1, 'failed': 2, 'stale': 3})
        self.assertEqual(len(requests), 2)
        self.assertIn('sent=1 stale=3 failed=2', logs.output[0])

    def test_timeout_is_not_retried_after_the_edge_request_may_have_been_received(self):
        requests = []

        class TimeoutServer:
            def request(self, method, path, payload=None, **kwargs):
                requests.append((method, path))
                if method == 'GET':
                    return [{
                        'id': 42, 'source': 'booking', 'status': 'confirmed',
                        'name': 'Mario Rossi', 'booking_date': '2026-10-08',
                        'booking_time': '20:15', 'party_size': 3,
                    }]
                raise TimeoutError('response lost after request')

        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': 'push-server-secret',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer', return_value=TimeoutServer()):
            with self.assertRaisesRegex(TimeoutError, 'response lost'):
                booking_push.send_new_online_booking_push(42)

        self.assertEqual(requests.count(('POST', '/functions/v1/web-push-admin')), 1)

    def test_requires_dedicated_server_secret_before_any_supabase_request(self):
        with patch.dict('os.environ', {
                'MAKAI_PUSH_SECRET': '',
                'SUPABASE_PUBLISHABLE_KEY': 'publishable-key',
        }), patch('booking_push.SupabaseServer') as server:
            with self.assertRaisesRegex(RuntimeError, 'Configurazione server'):
                booking_push.send_new_online_booking_push(42)
        server.assert_not_called()


if __name__ == '__main__':
    unittest.main()
