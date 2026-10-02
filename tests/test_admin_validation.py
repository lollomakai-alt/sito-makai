import sys
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from config import TZ
from bookings.validators import normalize_phone, normalize_booking_name
from bookings.service import create_admin_booking


class AdminValidationTests(unittest.TestCase):
    def test_contacts(self):
        for raw in ('34255678', '+39 34255678', '12345678', '333abc1234567', '+003331234567'):
            self.assertIsNone(normalize_phone(raw), raw)
        for raw, expected in (('333 123 4567', '+393331234567'), ('0039 3331234567', '+393331234567'), ('06 12345678', '+390612345678'), ('+44 7911 123456', '+447911123456')):
            self.assertEqual(normalize_phone(raw), expected)
        for raw in ('Marco', '123 Marco', 'Marco !!!'):
            self.assertIsNone(normalize_booking_name(raw))
        self.assertEqual(normalize_booking_name("  Nicolò  D’Angelo  "), 'Nicolò D’Angelo')

    def test_invalid_inputs_never_open_database(self):
        values = dict(name='Marco Rossi', phone='3331234567', email='', date='2026-10-06', time='21:00', party_size=4, notes='')
        cases = [dict(name='Marco'), dict(phone='34255678'), dict(email='marco gmail@gmail.com'), dict(time='21:15'), dict(time='25:00'), dict(party_size=2.5), dict(party_size=True), dict(party_size=0), dict(date='2026-02-30'), dict(date='2026-10-05'), dict(date='2026-10-01'), dict(notes='x' * 301)]
        with patch('bookings.service.db') as database, patch('bookings.validators.now_local', return_value=datetime(2026, 10, 2, 12, tzinfo=TZ)):
            for change in cases:
                with self.subTest(change=change):
                    self.assertFalse(create_admin_booking(**{**values, **change})['ok'])
            database.assert_not_called()
