import os
import sys
import unittest
from pathlib import Path


API_DIR = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("CHAT_SESSION_SECRET", "test-secret-for-chat-quick-replies-123456")

from automatic_chat import answer_chat  # noqa: E402
from prenotazioni import PHONE, _serializer  # noqa: E402


class ChatQuickRepliesTests(unittest.TestCase):
    def test_booking_and_availability_requests_redirect_without_writes(self):
        from unittest.mock import patch
        with patch("prenotazioni.create_booking") as create, patch("prenotazioni.check_availability") as availability:
            for message in ("Vorrei prenotare un tavolo", "Avete posti domani?", "Annulla la prenotazione"):
                result = answer_chat(message, None)
                self.assertIn("/prenotazioni", result["reply"])
                self.assertNotIn("show_booking_consents", result)
                self.assertEqual(_serializer().loads(result["session_token"])["step"], "assistente")
            create.assert_not_called()
            availability.assert_not_called()

    def test_old_confirmation_cannot_create_booking(self):
        from unittest.mock import patch
        from prenotazioni import QUESTIONS
        with patch("prenotazioni.create_booking") as create:
            for step in QUESTIONS:
                token = _serializer().dumps({"step": step, "nome": "Private name", "context": {"intent": "booking"}})
                result = answer_chat("Sì, confermo", token)
                self.assertIsNone(result["session_token"])
                self.assertIn("/prenotazioni", result["reply"])
                self.assertNotIn("Private name", result["reply"])
            create.assert_not_called()

    def test_dinner_and_aperitif_advance_after_guest_count(self):
        for category in ("Cena / apericena", "Aperitivo"):
            with self.subTest(category=category):
                first = answer_chat(category, None)
                self.assertIn("20 persone", first["quick_replies"])
                result = answer_chat("20 persone", first["session_token"])
                self.assertIn("20 persone", result["reply"])
                self.assertNotIn("Per quante persone", result["reply"])
                self.assertNotIn("20 persone", result["quick_replies"])
                self.assertIn(PHONE, result["reply"])

    def test_spaced_after_dinner_is_not_dinner(self):
        result = answer_chat("Dopo cena", None)
        state = _serializer().loads(result["session_token"])
        self.assertEqual(state["context"]["event"]["category"], "dopo cena")
        self.assertIn("Drink + torta", result["quick_replies"])

    def test_information_question_replaces_event_suggestions(self):
        first = answer_chat("Dopocena", None)
        result = answer_chat("Quali sono gli orari?", first["session_token"])
        self.assertEqual(result["quick_replies"], [])
        self.assertEqual(_serializer().loads(result["session_token"])["context"]["intent"], "info")

    def test_reset_exits_event_context(self):
        first = answer_chat("Dopocena", None)
        result = answer_chat("cambiamo argomento", first["session_token"])
        context = _serializer().loads(result["session_token"])["context"]
        self.assertNotIn("event", context)
        self.assertEqual(result["quick_replies"], [])

    def test_new_event_drops_old_guests(self):
        first = answer_chat("Aperitivo per 20 persone", None)
        result = answer_chat("Nuovo evento", first["session_token"])
        context = _serializer().loads(result["session_token"])["context"]
        self.assertNotIn("people", context)
        self.assertNotIn("people", context["event"])
        self.assertEqual(result["quick_replies"], ["Aperitivo", "Cena / apericena", "Dopocena"])

    def test_explicit_menu_with_people_overrides_event(self):
        from unittest.mock import patch
        first = answer_chat("Dopocena", None)
        with patch("automatic_chat.answer_menu", return_value="Informazioni sui cocktail") as menu:
            result = answer_chat("Consigliami cocktail per 2 persone", first["session_token"])
        menu.assert_called_once()
        self.assertEqual(result["quick_replies"], [])

    def test_unknown_replies_release_previous_event_choices(self):
        from unittest.mock import patch
        first = answer_chat("Dopocena", None)
        with patch("automatic_chat.get_menu_data", return_value={"menu": {}}):
            result = answer_chat("sì", first["session_token"])
            again = answer_chat("boh", result["session_token"])
        self.assertEqual(result["quick_replies"], [])
        self.assertEqual(again["quick_replies"], [])
        self.assertIn("Non ho capito", result["reply"])
        self.assertIn(PHONE, again["reply"])
        recovered = answer_chat("Quali sono gli orari?", again["session_token"])
        self.assertIn("23:30", recovered["reply"])
        self.assertNotIn("unrecognised_count", _serializer().loads(recovered["session_token"])["context"])

    def test_faq_leaves_event_suggestions(self):
        first = answer_chat("Dopocena", None)
        result = answer_chat("Accettate animali?", first["session_token"])
        self.assertIn(PHONE, result["reply"])
        self.assertEqual(result["quick_replies"], [])

    def test_invalid_session_still_answers_current_information_question(self):
        result = answer_chat("Quali sono gli orari?", "expired-or-invalid")
        self.assertIn("23:30", result["reply"])
        self.assertEqual(result["quick_replies"], [])

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
        self.assertIn("Per organizzare il dopocena contatta", packages["reply"])
        self.assertIn(PHONE, packages["reply"])

    def test_dopocena_joined_word_never_starts_dinner_booking(self):
        result = answer_chat("Vorrei prenotare dopocena", None)
        self.assertIn("Per organizzare il dopocena contatta", result["reply"])
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
        self.assertIsNone(result["session_token"])
        self.assertIn("/prenotazioni", result["reply"])


if __name__ == "__main__":
    unittest.main()
