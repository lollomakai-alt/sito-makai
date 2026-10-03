import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from fastapi.testclient import TestClient
import index
import admin_auth

TEST_SECRET = 'test-only-server-key-' * 3

class AgendaGatewayTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            'AGENDA_BACKEND_SECRET': TEST_SECRET,
            'SUPABASE_URL': 'https://auth.invalid',
            'SUPABASE_PUBLISHABLE_KEY': 'public-test-key',
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client = TestClient(index.app)

    def headers(self, key=TEST_SECRET):
        return {'Authorization': 'Bearer test-session', 'X-Agenda-Backend-Key': key}

    def user_response(self, body):
        response = io.BytesIO(body)
        return patch.object(admin_auth, 'urlopen', return_value=response)

    def test_direct_staff_token_without_gateway_is_denied(self):
        with patch.object(admin_auth, 'urlopen') as auth:
            response = self.client.get('/api/admin/session', headers={'Authorization': 'Bearer test-session'})
        self.assertEqual(response.status_code, 403)
        auth.assert_not_called()

    def test_wrong_key_is_denied(self):
        self.assertEqual(self.client.get('/api/admin/session', headers=self.headers('wrong')).status_code, 403)

    def test_missing_configuration_fails_closed(self):
        with patch.dict(os.environ, {'AGENDA_BACKEND_SECRET': ''}):
            self.assertEqual(self.client.get('/api/admin/session', headers=self.headers()).status_code, 503)

    def test_gateway_does_not_replace_user_authentication(self):
        error = HTTPError('https://auth.invalid', 401, 'Unauthorized', {}, None)
        with patch.object(admin_auth, 'urlopen', side_effect=error):
            self.assertEqual(self.client.get('/api/admin/session', headers=self.headers()).status_code, 401)

    def test_user_editable_role_is_not_trusted(self):
        with self.user_response(b'{"id":"customer","app_metadata":{},"user_metadata":{"role":"staff"}}'):
            self.assertEqual(self.client.get('/api/admin/session', headers=self.headers()).status_code, 403)

    def test_verified_staff_and_gateway_are_allowed(self):
        with self.user_response(b'{"id":"staff-id","app_metadata":{"role":"staff"}}'):
            response = self.client.get('/api/admin/session', headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'username': 'staff-id'})
        self.assertNotIn(TEST_SECRET, response.text)

    def test_legacy_login_is_also_protected(self):
        self.assertEqual(self.client.post('/api/admin/login', json={}).status_code, 403)

    def test_public_health_remains_accessible(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)

if __name__ == '__main__':
    unittest.main()
