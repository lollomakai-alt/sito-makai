import sys
import unittest
import os
from pathlib import Path


API_DIR = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("CHAT_SESSION_SECRET", "test-secret-for-email-confirmation-123456")

from automatic_chat import answer_chat  # noqa: E402
from bookings.validators import normalize_email  # noqa: E402
from prenotazioni import _serializer  # noqa: E402


class EmailValidationTests(unittest.TestCase):
    def test_accepts_uppercase_and_normalizes_to_lowercase(self):
        self.assertEqual(
            normalize_email("MARIO.ROSSI@GMAIL.COM"),
            "mario.rossi@gmail.com",
        )

    def test_accepts_an_address_written_with_spaces(self):
        self.assertEqual(
            normalize_email("Mario Rossi @ GMAIL . COM"),
            "mariorossi@gmail.com",
        )

    def test_rejects_invalid_addresses(self):
        invalid = (
            "mario.rossi gmail.com",
            "mario@@gmail.com",
            "mario@gmail",
            ".mario@gmail.com",
            "mario..rossi@gmail.com",
            "mario@gmail..com",
            "mario@-gmail.com",
        )
        for value in invalid:
            with self.subTest(value=value):
                self.assertIsNone(normalize_email(value))

    def test_chat_asks_to_confirm_the_normalized_email(self):
        token = _serializer().dumps({
            "mode": "booking",
            "step": "email",
            "started_at": 1_700_000_000,
            "persone": 2,
            "data": "2026-10-10",
            "ora": "20:00",
            "nome": "Mario Rossi",
            "telefono": "+393331234567",
            "checked": [2, "2026-10-10", "20:00"],
            "privacy_notice_shown": True,
            "context": {"intent": "booking"},
        })

        confirmation = answer_chat("Mario Rossi @ GMAIL . COM", token)
        self.assertIn("mariorossi@gmail.com", confirmation["reply"])
        self.assertEqual(
            confirmation["quick_replies"],
            ["Sì, confermo", "Cambia email"],
        )

        change = answer_chat("Cambia email", confirmation["session_token"])
        self.assertIn("Una email di riferimento", change["reply"])

        corrected = answer_chat("NUOVO INDIRIZZO @ TISCALI . IT", change["session_token"])
        self.assertIn("nuovoindirizzo@tiscali.it", corrected["reply"])
        self.assertEqual(
            corrected["quick_replies"],
            ["Sì, confermo", "Cambia email"],
        )

        notes = answer_chat("Sì, confermo", corrected["session_token"])
        self.assertIn("richieste particolari", notes["reply"])
        self.assertEqual(notes["quick_replies"], ["Nessuna nota"])


if __name__ == "__main__":
    unittest.main()
