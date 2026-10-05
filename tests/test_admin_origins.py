import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from fastapi import HTTPException
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
from admin_auth import require_browser_action
from origins import allowed_origins, AGENDA_PRODUCTION_ORIGIN


def browser_request(origin, host='backend.example', fetch_site='same-origin', action='1'):
    return Request({'type': 'http', 'method': 'POST', 'scheme': 'https',
                    'server': (host, 443), 'path': '/api/admin/bookings',
                    'headers': [(b'host', host.encode()), (b'origin', origin.encode()),
                                (b'x-admin-request', action.encode()),
                                (b'sec-fetch-site', fetch_site.encode())]})


class AdminOriginTests(unittest.TestCase):
    def test_production_allowed_even_with_existing_local_config(self):
        with patch.dict(os.environ, {'ALLOWED_ORIGINS': 'http://localhost:5173,http://localhost:3000'}):
            require_browser_action(browser_request(AGENDA_PRODUCTION_ORIGIN))
            self.assertIn(AGENDA_PRODUCTION_ORIGIN, allowed_origins())

    def test_unknown_origin_blocked(self):
        with patch.dict(os.environ, {'ALLOWED_ORIGINS': 'http://localhost:5173'}):
            for origin in ['https://unknown.example', 'https://agenda-makai.vercel.app.attacker.example', 'http://agenda-makai.vercel.app']:
                with self.subTest(origin=origin), self.assertRaises(HTTPException) as error:
                    require_browser_action(browser_request(origin))
                self.assertEqual(error.exception.status_code, 403)
                self.assertEqual(error.exception.detail, 'Origine non consentita.')

    def test_local_defaults_preserved(self):
        with patch.dict(os.environ, {}, clear=True):
            for origin in ['http://localhost:5173', 'http://localhost:3000']:
                require_browser_action(browser_request(origin))
                self.assertIn(origin, allowed_origins())
            # Vite's local proxy retains the browser Host on port 5174.
            require_browser_action(browser_request('https://localhost:5174', host='localhost:5174'))

    def test_configured_origins_preserved_and_wildcard_ignored(self):
        with patch.dict(os.environ, {'ALLOWED_ORIGINS': 'http://localhost:5174, http://127.0.0.1:4174/, *, https://custom.example'}):
            self.assertNotIn('*', allowed_origins())
            for origin in ['http://localhost:5174', 'http://127.0.0.1:4174', 'https://custom.example']:
                require_browser_action(browser_request(origin))
            with self.assertRaises(HTTPException):
                require_browser_action(browser_request('https://unknown.example'))

    def test_browser_action_protections_preserved(self):
        for kwargs in [{'action': ''}, {'fetch_site': 'cross-site'}]:
            with self.assertRaises(HTTPException) as error:
                require_browser_action(browser_request(AGENDA_PRODUCTION_ORIGIN, **kwargs))
            self.assertEqual(error.exception.status_code, 403)

    def test_cors_uses_same_explicit_allowlist(self):
        with patch.dict(os.environ, {'ALLOWED_ORIGINS': 'http://localhost:5173,*'}):
            middleware = CORSMiddleware(None, allow_origins=allowed_origins(), allow_methods=['GET', 'POST'])
            self.assertFalse(middleware.allow_all_origins)
            self.assertTrue(middleware.is_allowed_origin(AGENDA_PRODUCTION_ORIGIN))
            self.assertTrue(middleware.is_allowed_origin('http://localhost:5173'))
            self.assertFalse(middleware.is_allowed_origin('https://unknown.example'))
