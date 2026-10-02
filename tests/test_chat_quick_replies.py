import os
import sys
import unittest
from datetime import timedelta
from pathlib import Path


API_DIR = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("CHAT_SESSION_SECRET", "test-secret-for-chat-quick-replies-123456")

from automatic_chat import answer_chat  # noqa: E402
from bookings.dates import now_local  # noqa: E402
from config import CLOSED_WEEKDAYS  # noqa: E402
from prenotazioni import PHONE, _serializer, parse_data  # noqa: E402


class ChatQuickRepliesTests(unittest.TestCase):
    def test_booking_replies_follow_people_date_and_time_steps(self):
        people = answer_chat("Vorrei prenotare un tavolo", None)
        self.assertEqual(
            people["quick_replies"],
            ["2 persone", "3 persone", "4 persone", "5 persone"],
        )

        dates = answer_chat("2 persone", people["session_token"])
        self.assertEqual(len(dates["quick_replies"]), 4)
        for value in dates["quick_replies"]:
            day = parse_data(value)
            self.assertIsNotNone(day)
            self.assertNotIn(day.weekday(), CLOSED_WEEKDAYS)

        open_day = now_local().date() + timedelta(days=1)
        while open_day.weekday() in CLOSED_WEEKDAYS:
            open_day += timedelta(days=1)
        times = answer_chat(open_day.strftime("%d/%m/%Y"), dates["session_token"])
        self.assertEqual(times["quick_replies"], ["18:00", "19:30", "21:00", "22:30"])

    def test_event_package_replies_follow_selected_time_band(self):
        categories = answer_chat("Vorrei sapere i pacchetti festa", None)
        self.assertEqual(
            categories["quick_replies"],
            ["Aperitivo", "Cena / apericena", "Dopocena"],
        )

        packages = answer_chat("Dopocena", categories["session_token"])
        self.assertEqual(
            packages["quick_replies"],
            ["Drink + torta", "Drink + snack", "Drink + prosecco"],
        )
        self.assertIn("dalle 22:30 alle 00:00", packages["reply"])
        self.assertIn("chiude alle 02:00", packages["reply"])
        self.assertIn("prenotazioni automatiche solo per la cena", packages["reply"])
        self.assertIn(PHONE, packages["reply"])

    def test_dopocena_joined_word_never_starts_dinner_booking(self):
        result = answer_chat("Vorrei prenotare dopocena", None)
        self.assertIn("prenotazioni automatiche solo per la cena", result["reply"])
        self.assertIn(PHONE, result["reply"])
        self.assertEqual(
            result["quick_replies"],
            ["Drink + torta", "Drink + snack", "Drink + prosecco"],
        )

    def test_event_package_selection_keeps_people_step(self):
        categories = answer_chat("Vorrei sapere i pacchetti festa", None)
        packages = answer_chat("Dopocena", categories["session_token"])
        selected = answer_chat("Drink + torta", packages["session_token"])

        self.assertIn("Per quante persone", selected["reply"])
        self.assertEqual(
            selected["quick_replies"],
            ["10 persone", "15 persone", "20 persone", "30 persone"],
        )

        people = answer_chat("20 persone", selected["session_token"])
        self.assertIn("20", people["reply"])
        self.assertIn("persone", people["reply"].lower())

    def test_personal_contact_steps_hide_unrelated_questions(self):
        token = _serializer().dumps({
            "mode": "booking",
            "step": "nome",
            "started_at": 1_700_000_000,
            "persone": 2,
            "data": "2026-10-10",
            "ora": "20:00",
            "checked": [2, "2026-10-10", "20:00"],
            "context": {"intent": "booking"},
        })
        result = answer_chat("Mario Rossi", token)
        self.assertEqual(result["quick_replies"], [])


if __name__ == "__main__":
    unittest.main()
