import os
import sys
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


API_DIR = Path(__file__).resolve().parents[1] / 'api'
sys.path.insert(0, str(API_DIR))
os.environ.setdefault('CHAT_SESSION_SECRET', 'test-secret-for-booking-privacy-123456789')

import bookings.service as booking_service  # noqa: E402
from automatic_chat import answer_chat  # noqa: E402
from prenotazioni import PRIVACY_NOTICE, QUESTIONS, _advance, _handle, _serializer  # noqa: E402


def complete_state(**overrides):
    state = {
        'mode': 'booking',
        'step': 'note',
        'started_at': 1_700_000_000,
        'persone': 2,
        'data': '2026-10-10',
        'ora': '20:00',
        'checked': [2, '2026-10-10', '20:00'],
        'nome': 'Monkey Luffy',
        'telefono': '+393331234567',
        'email': 'luffy@example.com',
        'email_confermata': True,
        'note': '',
        'privacy_notice_shown': True,
    }
    state.update(overrides)
    return state


class FakeConnection:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        return self

    def fetchone(self):
        return {'id': 77}


class MarketingConnection:
    def __init__(self):
        self.calls = []
        self.query = ''

    def execute(self, query, params=()):
        self.query = query
        self.calls.append((query, params))
        return self

    def fetchone(self):
        if 'FROM bookings' in self.query:
            return {'id': 77, 'name': 'Monkey Luffy', 'email': 'luffy@example.com',
                    'phone': '+393331234567', 'arrived_at': None,
                    'marketing_visit_counted_at': None}
        if 'SELECT id FROM marketing_contacts' in self.query:
            return {'id': 12}
        if 'UPDATE marketing_contacts' in self.query:
            return {'id': 12, 'consenso_data': datetime(2026, 10, 1, 12, 0),
                    'scadenza_consenso': datetime(2028, 10, 1, 12, 0), 'rinnovi': 2,
                    'visite_totali': 3}
        return None


class ArrivalConnection:
    def __init__(self):
        self.calls = []
        self.query = ''

    def execute(self, query, params=()):
        self.query = query
        self.calls.append((query, params))
        return self

    def fetchone(self):
        if 'UPDATE bookings SET arrived_at' in self.query:
            return {'id': 77, 'email': 'luffy@example.com', 'phone': '+393331234567',
                    'arrived_at': datetime(2026, 10, 10, 20, 0),
                    'marketing_visit_counted_at': None}
        if 'SELECT id, visite_totali FROM marketing_contacts' in self.query:
            return {'id': 12, 'visite_totali': 3}
        if 'UPDATE marketing_contacts SET visite_totali' in self.query:
            return {'visite_totali': 4}
        return None


class BookingPrivacyTests(unittest.TestCase):
    def test_privacy_notice_is_shown_once_before_contact_questions(self):
        state = complete_state(
            step='nome',
            privacy_notice_shown=False,
        )
        for field in ('nome', 'telefono', 'email', 'note'):
            state.pop(field, None)

        first = _advance(state)
        self.assertIn(PRIVACY_NOTICE, first['reply'])
        self.assertIn(QUESTIONS['nome'], first['reply'])

        state['nome'] = 'Monkey Luffy'
        second = _advance(state)
        self.assertNotIn(PRIVACY_NOTICE, second['reply'])
        self.assertIn(QUESTIONS['telefono'], second['reply'])

    def test_optional_consents_default_to_false_and_are_passed_to_insert(self):
        state = complete_state(step='note')
        question = _handle(state, 'nessuna', lambda _: None)
        self.assertEqual(state['step'], 'consensi')
        self.assertEqual(question['reply'], QUESTIONS['consensi'])

        summary = _handle(state, 'continua', lambda _: None)
        self.assertFalse(state['consenso_ricordami'])
        self.assertEqual(state['step'], 'conferma')
        self.assertIn('Ricordare nome e telefono per 12 mesi: no.', summary['reply'])

        result = {
            'ok': True,
            'party_size': 2,
            'date': '2026-10-10',
            'time': '20:00',
            'name': 'Monkey Luffy',
        }
        with patch('prenotazioni.create_booking', return_value=result) as create:
            _handle(state, 'sì', lambda _: None)
        self.assertFalse(create.call_args.kwargs['consenso_ricordami'])

    def test_checkbox_values_survive_the_automatic_chat_signed_session(self):
        state = complete_state(step='consensi', context={})
        token = _serializer().dumps(state)
        result = answer_chat(
            'continua',
            token,
            consenso_ricordami=True,
        )
        updated = _serializer().loads(result['session_token'])
        self.assertTrue(updated['consenso_ricordami'])
        self.assertEqual(updated['step'], 'conferma')

    def test_frontend_is_told_to_show_consent_checkboxes_before_summary(self):
        state = complete_state(step='note', context={})
        token = _serializer().dumps(state)
        result = answer_chat('nessuna', token)
        updated = _serializer().loads(result['session_token'])
        self.assertEqual(updated['step'], 'consensi')
        self.assertTrue(result['show_booking_consents'])

    def test_insert_saves_utc_consent_timestamp_and_leaves_expiry_to_trigger(self):
        connection = FakeConnection()

        @contextmanager
        def fake_db(write=False):
            self.assertTrue(write)
            yield connection

        booking_datetime = datetime(2026, 10, 10, 20, 0)
        with (
            patch.object(booking_service, 'db', fake_db),
            patch.object(booking_service, '_validate', return_value=(booking_datetime, None)),
            patch.object(booking_service, '_upcoming_for_phone', return_value=[]),
            patch.object(booking_service, '_find_tables', return_value=['10']),
        ):
            result = booking_service.create_booking(
                name='Monkey Luffy',
                email='luffy@example.com',
                phone='+393331234567',
                date='2026-10-10',
                time='20:00',
                party_size=2,
                consenso_ricordami=True,
            )

        self.assertTrue(result['ok'])
        query, params = connection.calls[-1]
        self.assertIn('consenso_ricordami, consenso_data', query)
        self.assertNotIn('scadenza_dati', query)
        self.assertIn('CASE WHEN %s THEN now() ELSE NULL END', query)
        self.assertIs(params[-2], True)
        self.assertIs(params[-1], True)

    def test_insert_without_consent_saves_false_and_null_date(self):
        connection = FakeConnection()

        @contextmanager
        def fake_db(write=False):
            yield connection

        with (
            patch.object(booking_service, 'db', fake_db),
            patch.object(booking_service, '_validate', return_value=(datetime(2026, 10, 10, 20, 0), None)),
            patch.object(booking_service, '_upcoming_for_phone', return_value=[]),
            patch.object(booking_service, '_find_tables', return_value=['10']),
        ):
            booking_service.create_booking(
                name='Monkey Luffy',
                email='luffy@example.com',
                phone='+393331234567',
                date='2026-10-10',
                time='20:00',
                party_size=2,
            )

        _, params = connection.calls[-1]
        self.assertIs(params[-2], False)
        self.assertIs(params[-1], False)

    def test_manual_insert_is_staff_source_and_does_not_acquire_consent(self):
        connection = FakeConnection()

        @contextmanager
        def fake_db(write=False):
            self.assertTrue(write)
            yield connection

        with (
            patch.object(booking_service, 'db', fake_db),
            patch.object(booking_service, '_validate', return_value=(datetime(2026, 10, 10, 20, 0), None)),
            patch.object(booking_service, '_upcoming_for_phone', return_value=[]),
            patch.object(booking_service, '_find_tables', return_value=['10']),
        ):
            result = booking_service.create_admin_booking(
                name='Monkey Luffy',
                email='',
                phone='+393331234567',
                date='2026-10-10',
                time='20:00',
                party_size=2,
                notes='Compleanno',
            )

        self.assertTrue(result['ok'])
        query, params = connection.calls[-1]
        self.assertIn("'staff'", query)
        self.assertNotIn('consenso_ricordami', query)
        self.assertNotIn('consenso_data', query)
        self.assertNotIn('scadenza_dati', query)
        self.assertEqual(params[1], '')

    def test_repeated_marketing_consent_restarts_twenty_four_month_period(self):
        connection = MarketingConnection()

        @contextmanager
        def fake_db(write=False):
            self.assertTrue(write)
            yield connection

        with patch.object(booking_service, 'db', fake_db):
            result = booking_service.register_marketing_consent(
                booking_id=77,
                channel='whatsapp',
                response_text='Confermo',
                recorded_by='admin',
            )

        self.assertTrue(result['ok'])
        self.assertEqual(result['renewals'], 2)
        update_query = next(query for query, _ in connection.calls if 'UPDATE marketing_contacts' in query)
        self.assertIn("consenso_data=now()", update_query)
        self.assertIn("scadenza_consenso=now()+interval '24 months'", update_query)
        self.assertIn("revocato_il=NULL", update_query)
        self.assertIn("rinnovi=rinnovi+1", update_query)

    def test_marketing_consent_rejects_thanks_without_an_affirmative_answer(self):
        result = booking_service.register_marketing_consent(
            booking_id=77,
            channel='whatsapp',
            response_text='Grazie',
            recorded_by='admin',
        )
        self.assertFalse(result['ok'])
        self.assertIn('Grazie da solo non basta', result['error'])

    def test_arrival_increments_active_marketing_contact_once(self):
        connection = ArrivalConnection()

        @contextmanager
        def fake_db(write=False):
            self.assertTrue(write)
            yield connection

        with patch.object(booking_service, 'db', fake_db):
            result = booking_service.mark_arrived(77)

        self.assertTrue(result['ok'])
        self.assertTrue(result['visit_counted'])
        self.assertEqual(result['visits'], 4)
        counted_updates = [query for query, _ in connection.calls
                           if 'UPDATE marketing_contacts SET visite_totali' in query]
        marker_updates = [query for query, _ in connection.calls
                          if 'marketing_visit_counted_at=now()' in query]
        self.assertEqual(len(counted_updates), 1)
        self.assertEqual(len(marker_updates), 1)


if __name__ == '__main__':
    unittest.main()
