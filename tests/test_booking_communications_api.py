import io
import json
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from fastapi.testclient import TestClient
import index
import admin_auth
import supabase_server
import booking_communications

SECRET = 'test-only-gateway-secret-' * 3
SERVICE_KEY = 'test-only-service-role-secret'
BASE = '/api/admin/bookings/42'
ROUTES = [('GET', BASE + '/communications'), ('POST', BASE + '/communications/prepare'),
          ('POST', BASE + '/send-confirmation-email')]


class CommunicationApiTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {'AGENDA_BACKEND_SECRET': SECRET,
            'SUPABASE_URL': 'https://example.supabase.co', 'SUPABASE_PUBLISHABLE_KEY': 'public-key',
            'SUPABASE_SERVICE_ROLE_KEY': SERVICE_KEY})
        environment.start(); self.addCleanup(environment.stop)
        self.client = TestClient(index.app)
        self.headers = {'Authorization': 'Bearer admin-session', 'X-Agenda-Backend-Key': SECRET,
            'X-Admin-Request': '1', 'Origin': 'https://agenda-makai.vercel.app', 'Sec-Fetch-Site': 'same-origin'}
        self.booking = [{'id': 42, 'status': 'confirmed'}]
        self.row = {'id': 1, 'booking_id': 42, 'channel': 'email', 'status': 'queued',
                    'kind': 'confirmation', 'debug': SERVICE_KEY}
        self.result = {'bookingId': 42, 'type': 'booking_confirmation', 'status': 'accepted',
                       'emailId': 'email-id', 'communicationId': 1, 'debug': SERVICE_KEY}
        self.outbound = []
        self.logs = []
        self.edge_failure = self.finish_failure = self.claim_failure = None
        self.claim_barrier = None
        self.claim_lock = Lock()
        self.opener = MagicMock()
        self.opener.open.side_effect = self.transport
        opener_patch = patch.object(supabase_server, 'build_opener', return_value=self.opener)
        opener_patch.start(); self.addCleanup(opener_patch.stop)

    def transport(self, request, timeout):
        self.outbound.append(request)
        # Every DB/RPC/Edge request must use the server secret, never the admin JWT.
        self.assertEqual(request.get_header('Authorization'), 'Bearer ' + SERVICE_KEY)
        self.assertEqual(request.get_header('Apikey'), SERVICE_KEY)
        self.assertIsNone(request.get_header('X-agenda-backend-key'))
        self.assertIsInstance(supabase_server.build_opener.call_args.args[0], supabase_server.NoRedirect)
        self.assertEqual(timeout, 20)
        if '/rest/v1/bookings?' in request.full_url:
            result = self.booking
        elif '/rest/v1/booking_communications?' in request.full_url:
            result = [self.row]
        elif request.full_url.endswith('/rpc/admin_prepare_booking_communication'):
            result = self.row
        elif request.full_url.endswith('/rpc/claim_booking_email'):
            if self.claim_failure:
                raise self.claim_failure
            if self.claim_barrier:
                self.claim_barrier.wait(timeout=5)
            with self.claim_lock:
                if self.row['status'] in ['queued', 'failed']:
                    self.row['status'] = 'sending'
                    result = self.row.copy()
                else:
                    result = None
        elif request.full_url.endswith('/rpc/claim_new_online_booking_email'):
            with self.claim_lock:
                if self.row['status'] == 'queued':
                    self.row['status'] = 'sending'
                    result = self.row.copy()
                else:
                    result = None
        elif request.full_url.endswith('/functions/v1/send-booking-email'):
            if self.edge_failure:
                raise self.edge_failure
            result = self.result
        elif request.full_url.endswith('/rpc/finish_booking_email'):
            if self.finish_failure:
                raise self.finish_failure
            args = json.loads(request.data)
            self.logs.append(args)
            self.row['status'] = args['p_status']
            self.row['provider_id'] = args['p_provider_id']
            return io.BytesIO(b'')  # A successful void RPC may have no JSON body.
        else:
            self.fail('Unexpected Supabase endpoint')
        return io.BytesIO(json.dumps(result).encode())

    def auth(self, role='admin'):
        user = {'id': 'admin-id', 'app_metadata': {'role': role}, 'user_metadata': {'role': 'admin'}}
        return patch.object(admin_auth, 'urlopen', side_effect=lambda *a, **kw: io.BytesIO(json.dumps(user).encode()))

    def test_authorized_admin_can_list_using_service_role(self):
        with self.auth() as auth:
            response = self.client.get(ROUTES[0][1], headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'communications': [{k: v for k, v in self.row.items() if k != 'debug'}]})
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertIn('/rest/v1/booking_communications?', self.outbound[-1].full_url)
        self.assertIn('booking_id=eq.42', self.outbound[-1].full_url)
        auth_request = auth.call_args.args[0]
        self.assertEqual(auth_request.full_url, 'https://example.supabase.co/auth/v1/user')
        self.assertEqual(auth_request.get_header('Authorization'), 'Bearer admin-session')
        self.assertEqual(auth_request.get_header('Apikey'), 'public-key')

    def test_public_and_non_admin_blocked_before_privileged_access(self):
        for method, route in ROUTES:
            self.assertEqual(self.client.request(method, route).status_code, 403)
            for role in ['staff', 'customer', '']:
                with self.auth(role):
                    self.assertEqual(self.client.request(method, route, headers=self.headers).status_code, 403)
        self.opener.open.assert_not_called()

    def test_invalid_origin_is_blocked(self):
        with patch.object(admin_auth, 'urlopen') as auth:
            for method, route in ROUTES:
                response = self.client.request(method, route, headers={**self.headers, 'Origin': 'https://unknown.example'})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['detail'], 'Origine non consentita.')
            auth.assert_not_called(); self.opener.open.assert_not_called()

    def test_gateway_and_admin_token_required(self):
        for method, route in ROUTES:
            for override, expected in [({'X-Agenda-Backend-Key': ''}, 403), ({'Authorization': ''}, 401)]:
                with patch.object(admin_auth, 'urlopen') as auth:
                    response = self.client.request(method, route, headers={**self.headers, **override})
                    self.assertEqual(response.status_code, expected)
                    auth.assert_not_called()
        self.opener.open.assert_not_called()

    def test_expired_admin_session_blocked(self):
        with patch.object(admin_auth, 'urlopen', side_effect=HTTPError('https://example.supabase.co', 401, '', {}, None)):
            self.assertEqual(self.client.get(ROUTES[0][1], headers=self.headers).status_code, 401)
        self.opener.open.assert_not_called()

    def test_missing_booking_is_404_for_all_endpoints(self):
        self.booking = []
        for method, route in ROUTES:
            with self.auth():
                self.assertEqual(self.client.request(method, route, headers=self.headers).status_code, 404)
        self.assertEqual(len(self.outbound), 3)
        self.assertTrue(all('/rest/v1/bookings?' in req.full_url for req in self.outbound))

    def test_prepare_uses_service_role_and_migration_rpc(self):
        with self.auth():
            response = self.client.post(ROUTES[1][1], headers=self.headers, json={'channel': 'email'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SERVICE_KEY, response.text)
        self.assertEqual(self.outbound[-1].full_url, 'https://example.supabase.co/rest/v1/rpc/admin_prepare_booking_communication')
        self.assertEqual(json.loads(self.outbound[-1].data), {'p_booking_id': 42, 'p_channel': 'email'})

    def test_prepare_default_channel_and_whatsapp(self):
        for channel in ['email', 'whatsapp']:
            self.row['channel'] = channel
            with self.auth():
                response = self.client.post(ROUTES[1][1], headers=self.headers,
                    **({} if channel == 'email' else {'json': {'channel': channel}}))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(self.outbound[-1].data), {'p_booking_id': 42, 'p_channel': channel})

    def test_first_send_prepares_claims_calls_edge_and_logs_accepted(self):
        with self.auth():
            response = self.client.post(ROUTES[2][1], headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'accepted')
        self.assertNotIn(SERVICE_KEY, response.text)
        self.assertEqual([req.full_url.split('supabase.co')[1].split('?')[0] for req in self.outbound], [
            '/rest/v1/bookings', '/rest/v1/rpc/admin_prepare_booking_communication',
            '/rest/v1/rpc/claim_booking_email', '/functions/v1/send-booking-email', '/rest/v1/rpc/finish_booking_email'])
        self.assertEqual(json.loads(self.outbound[1].data), {'p_booking_id': 42, 'p_channel': 'email'})
        self.assertEqual(json.loads(self.outbound[2].data), {'p_id': 1})
        self.assertEqual(json.loads(self.outbound[3].data),
            {'bookingId': 42, 'type': 'booking_confirmation', 'communicationId': 1})
        self.assertEqual(self.logs, [{'p_id': 1, 'p_status': 'accepted', 'p_provider_id': 'email-id', 'p_error_code': None}])

    def test_double_send_blocked_by_null_claim(self):
        with self.auth():
            self.assertEqual(self.client.post(ROUTES[2][1], headers=self.headers).status_code, 200)
            second = self.client.post(ROUTES[2][1], headers=self.headers)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(len(self.edge_requests()), 1)
        self.assertEqual(len(self.logs), 1)

    def edge_requests(self):
        return [req for req in self.outbound if '/functions/v1/' in req.full_url]

    def test_edge_rejection_logged_failed_and_retry_uses_same_communication(self):
        self.edge_failure = HTTPError('https://example.supabase.co', 422, SERVICE_KEY, {}, io.BytesIO(SERVICE_KEY.encode()))
        with self.auth():
            response = self.client.post(ROUTES[2][1], headers=self.headers)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['status'], 'failed')
        self.assertEqual(self.logs[-1]['p_error_code'], 'edge_http_422')
        self.assertEqual(len(self.edge_requests()), 1)
        self.edge_failure = None
        with self.auth():
            self.assertEqual(self.client.post(ROUTES[2][1], headers=self.headers).status_code, 200)
        self.assertEqual([json.loads(req.data)['communicationId'] for req in self.edge_requests()], [1, 1])

    def test_uncertain_transport_or_edge_outcome_logged_unknown_and_blocks_retry(self):
        for failure in [URLError(SERVICE_KEY), TimeoutError(SERVICE_KEY),
                        HTTPError('https://example.supabase.co', 500, SERVICE_KEY, {}, None),
                        HTTPError('https://example.supabase.co', 409, SERVICE_KEY, {}, None), ValueError(SERVICE_KEY)]:
            self.row['status'] = 'queued'; self.edge_failure = failure
            before = len(self.edge_requests())
            with self.auth():
                response = self.client.post(ROUTES[2][1], headers=self.headers)
                retry = self.client.post(ROUTES[2][1], headers=self.headers)
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json()['status'], 'unknown')
            self.assertNotIn(SERVICE_KEY, response.text)
            self.assertEqual(self.logs[-1]['p_status'], 'unknown')
            self.assertEqual(retry.status_code, 409)
            self.assertEqual(len(self.edge_requests()), before + 1)

    def test_structured_edge_failed_unknown_and_error_code_sanitizing(self):
        for state, code, expected in [('failed','provider_http_422','provider_http_422'),
                                     ('unknown','network_uncertain','network_uncertain'),
                                     ('failed',SERVICE_KEY,'edge_failed')]:
            self.row['status'] = 'queued'
            self.result.update(status=state, emailId=None, errorCode=code)
            with self.auth():
                response = self.client.post(ROUTES[2][1], headers=self.headers)
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json()['status'], state)
            self.assertEqual(self.logs[-1]['p_error_code'], expected)
            self.assertNotIn(SERVICE_KEY, response.text)

    def test_booking_without_email_skipped_and_non_confirmed_blocked(self):
        self.row['status'] = 'skipped'
        with self.auth():
            response = self.client.post(ROUTES[2][1], headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(self.outbound), 2)
        for state in ['arrived', 'completed', 'cancelled', 'no_show', None]:
            self.booking[0]['status'] = state
            before = len(self.outbound)
            with self.auth():
                response = self.client.post(ROUTES[2][1], headers=self.headers)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(len(self.outbound), before + 1)
        self.assertEqual(len(self.edge_requests()), 0)
        self.assertEqual(self.logs, [])

    def test_failed_finish_keeps_sending_blocked_and_never_resends(self):
        self.finish_failure = URLError(SERVICE_KEY)
        with self.auth():
            response = self.client.post(ROUTES[2][1], headers=self.headers)
            retry = self.client.post(ROUTES[2][1], headers=self.headers)
        self.assertEqual(response.status_code, 502)
        self.assertIn('Esito email non registrato', response.text)
        self.assertNotIn(SERVICE_KEY, response.text)
        self.assertEqual(self.row['status'], 'sending')
        self.assertEqual(retry.status_code, 409)
        self.assertEqual(len(self.edge_requests()), 1)

    def test_concurrent_http_requests_only_claim_winner_sends_and_logs(self):
        # Two real concurrent HTTP handlers; emulate atomic SQL with a lock.
        # Actual SQL claim/permissions/transitions are also covered by PGlite.
        self.claim_barrier = Barrier(2)
        def send():
            client = TestClient(index.app)
            return client.post(ROUTES[2][1], headers=self.headers).status_code
        with self.auth(), ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(send), pool.submit(send)]
            statuses = [future.result(timeout=10) for future in futures]
        self.assertEqual(sorted(statuses), [200, 409])
        self.assertEqual(len(self.edge_requests()), 1)
        self.assertEqual(len(self.logs), 1)

    def test_null_or_failed_claim_never_invokes_edge_or_finish(self):
        for state in ['sending', 'accepted', 'unknown', 'superseded']:
            self.row['status'] = state
            with self.auth():
                self.assertEqual(self.client.post(ROUTES[2][1], headers=self.headers).status_code, 409)
        self.row['status'] = 'queued'; self.claim_failure = URLError(SERVICE_KEY)
        with self.auth():
            self.assertEqual(self.client.post(ROUTES[2][1], headers=self.headers).status_code, 502)
        self.assertEqual(len(self.edge_requests()), 0)
        self.assertEqual(self.logs, [])

    def test_client_cannot_override_server_key_or_email_payload(self):
        with self.auth():
            response = self.client.get(ROUTES[0][1], headers={**self.headers, 'apikey': 'browser-override'})
        self.assertEqual(response.status_code, 200)
        self.opener.open.reset_mock()
        for route in [ROUTES[1][1], ROUTES[2][1]]:
            for extra in [{'recipient': 'other@example.com'}, {'subject': 'custom'}, {'html': '<b>custom</b>'},
                          {'bookingId': 99}, {'communicationId': 99}, {'type': 'other'}, {'service_role_key': 'browser-override'}]:
                with self.auth():
                    self.assertEqual(self.client.post(route, headers=self.headers, json=extra).status_code, 422)
        self.opener.open.assert_not_called()

    def test_unconfigured_server_or_unsafe_url_block_privileged_access(self):
        for config in [{'SUPABASE_SERVICE_ROLE_KEY': ''}, {'SUPABASE_URL': 'http://example.supabase.co'},
                       {'SUPABASE_URL': 'https://example.supabase.co/path'},
                       {'SUPABASE_URL': 'https://user:password@example.supabase.co'},
                       {'SUPABASE_URL': 'https://example.supabase.co?query=1'},
                       {'SUPABASE_URL': 'https://['}, {'SUPABASE_URL': 'https://example.supabase.co:wrong'},
                       {'SUPABASE_SERVICE_ROLE_KEY': 'invalid\nkey'}]:
            with patch.dict(os.environ, config), self.auth():
                response = self.client.get(ROUTES[0][1], headers=self.headers)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(SERVICE_KEY, response.text)
        self.opener.open.assert_not_called()

    def test_upstream_errors_sanitized_without_retry_or_logging_secrets(self):
        for method, route in ROUTES:
            for failure in [HTTPError('https://example.supabase.co', 422, SERVICE_KEY, {}, io.BytesIO(SERVICE_KEY.encode())),
                            HTTPError('https://example.supabase.co', 302, SERVICE_KEY, {'Location': 'https://attacker.example'}, None),
                            URLError(SERVICE_KEY), TimeoutError(SERVICE_KEY), ValueError(SERVICE_KEY)]:
                self.opener.open.side_effect = [io.BytesIO(b'[{"id":42,"status":"confirmed"}]'), failure]
                self.opener.open.reset_mock()
                with self.auth(), self.assertLogs('httpx', level='INFO') as logs:
                    response = self.client.request(method, route, headers=self.headers)
                self.assertIn(response.status_code, [422, 502])
                self.assertNotIn(SERVICE_KEY, response.text)
                self.assertNotIn(SERVICE_KEY, ''.join(logs.output))
                self.assertEqual(self.opener.open.call_count, 2)
        self.assertIsNone(supabase_server.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://attacker.example'))

    def test_malformed_or_wrong_booking_upstream_is_rejected(self):
        for booking in [None, {}, [{'id': 99}], [{'id': 42}, {'id': 42}]]:
            self.booking = booking
            with self.auth():
                response = self.client.get(ROUTES[0][1], headers=self.headers)
            self.assertEqual(response.status_code, 502)

    def test_wrong_communication_and_edge_identity_rejected(self):
        self.row['booking_id'] = 99
        for method, route in ROUTES[:2]:
            with self.auth():
                self.assertEqual(self.client.request(method, route, headers=self.headers).status_code, 502)
        for patch_result in [{'bookingId': 99}, {'communicationId': 99}, {'emailId': ''}, {'type': 'other'}]:
            self.row['status'] = 'queued'; self.row['booking_id'] = 42
            previous = self.result.copy(); self.result.update(patch_result)
            with self.auth():
                self.assertEqual(self.client.post(ROUTES[2][1], headers=self.headers).status_code, 502)
            self.assertEqual(self.logs[-1]['p_status'], 'unknown')
            self.result = previous

    def test_invalid_id_does_not_reach_server(self):
        with self.auth():
            self.assertEqual(self.client.get('/api/admin/bookings/0/communications', headers=self.headers).status_code, 422)
        self.opener.open.assert_not_called()

    def test_automatic_send_claims_created_online_event_and_uses_shared_transport(self):
        booking_communications.send_new_online_booking_email(42)
        self.assertEqual(self.row['status'], 'accepted')
        self.assertEqual(len(self.edge_requests()), 1)
        self.assertEqual(self.logs[-1]['p_status'], 'accepted')
        self.assertEqual(json.loads(self.outbound[0].data), {'p_booking_id': 42})
        self.assertNotIn('/rpc/admin_prepare_booking_communication', ''.join(r.full_url for r in self.outbound))
        booking_communications.send_new_online_booking_email(42)
        self.assertEqual(len(self.edge_requests()), 1)

    def test_automatic_failure_is_logged_without_retries_or_propagating_to_booking(self):
        for failure, expected in [(HTTPError('https://example.supabase.co',422,SERVICE_KEY,{},None),'failed'),
                                  (TimeoutError(SERVICE_KEY),'unknown')]:
            self.row['status'] = 'queued'; self.edge_failure = failure
            before = len(self.edge_requests())
            with self.assertLogs('makai', level='WARNING') as logs:
                booking_communications.send_new_online_booking_email(42)
            self.assertEqual(self.logs[-1]['p_status'], expected)
            self.assertNotIn(SERVICE_KEY, ''.join(logs.output))
            booking_communications.send_new_online_booking_email(42)
            self.assertEqual(len(self.edge_requests()), before + 1)

    def test_automatic_configuration_or_finish_failure_never_propagates(self):
        with patch.dict(os.environ, {'SUPABASE_SERVICE_ROLE_KEY':''}), self.assertLogs('makai',level='WARNING'):
            booking_communications.send_new_online_booking_email(42)
        self.assertEqual(len(self.outbound), 0)
        self.finish_failure = TimeoutError(SERVICE_KEY)
        with self.assertLogs('makai', level='WARNING'):
            booking_communications.send_new_online_booking_email(42)
        self.assertEqual(self.row['status'], 'sending')
        booking_communications.send_new_online_booking_email(42)
        self.assertEqual(len(self.edge_requests()), 1)
