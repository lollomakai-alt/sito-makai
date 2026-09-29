import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch


API_DIR = Path(__file__).resolve().parents[1] / 'api'
sys.path.insert(0, str(API_DIR))
os.environ.setdefault('CHAT_SESSION_SECRET', 'test-secret-for-chat-menu-context-123456789')

from automatic_chat import _serializer, answer_chat  # noqa: E402
from chat_language import dietary_preferences  # noqa: E402
from chat_menu import (  # noqa: E402
    FOOD,
    answer_menu,
    build_current_request,
    filter_menu_items,
)


def menu_item(item_id, name, description, price, category):
    return {
        'id': item_id,
        'name_it': name,
        'description_it': description,
        'price': price,
        'category': category,
    }


class ChatMenuContextTests(unittest.TestCase):
    def setUp(self):
        self.menu = {
            'menu': {
                'snack': [
                    menu_item('beef', 'Beef Burger', 'Hamburger di manzo e bacon', 14.0, 'Snack'),
                    menu_item('chicken', 'Spiedini di pollo', 'Pollo marinato e verdure', 12.0, 'Snack'),
                    menu_item('veg', 'Poke vegetariana', 'Piatto vegetariano con verdure', 11.0, 'Snack'),
                ],
                'sushi': [
                    menu_item('salmon', 'Salmon Roll', 'Riso, alga e salmone', 13.0, 'Sushi'),
                    menu_item('tuna', 'Tuna Tataki', 'Tonno scottato e sesamo', 15.0, 'Sushi'),
                ],
                'primi_starters': [
                    menu_item('calamari', 'Calamari speziati', 'Calamari e spezie', 12.5, 'Primi'),
                ],
                'secondi_main': [],
                'dolci': [],
                'cocktails': [
                    menu_item('rum', 'Rum Punch', 'Rum scuro, ananas e lime', 10.0, 'Cocktail'),
                    menu_item('gin', 'Gin Wave', 'Gin, tonica e lime', 10.0, 'Cocktail'),
                ],
                'analcolici': [
                    menu_item('virgin', 'Virgin Mango', 'Mango, lime e soda', 8.0, 'Analcolico'),
                ],
                'volcanoes': [
                    menu_item('volcano', 'Volcano Rum', 'Rum e succhi tropicali', 24.0, 'Volcanoes'),
                ],
            }
        }
        self.choice = patch('chat_menu.random.choice', side_effect=lambda items: items[0])
        self.choice.start()
        self.addCleanup(self.choice.stop)

    def ask(self, message, context=None):
        if context is None:
            context = {}
        reply = answer_menu(message, context, lambda: self.menu, '06 000000')
        return reply, context

    def filtered_names(self, message, context=None, preferences=()):
        if context is None:
            context = {}
        request = build_current_request(message.lower(), context)
        items = [item for key in FOOD for item in self.menu['menu'].get(key, [])]
        return {
            item['name_it']
            for item in filter_menu_items(items, request, preferences)
        }

    def test_carne_overrides_old_vegetarian_filter(self):
        context = {
            'intent': 'cocktail',
            'menu_topic': 'cocktail',
            'preferences': ['vegetariano'],
            'active_menu_request': {'category': 'cocktail', 'alcohol_free': True},
        }
        reply, context = self.ask('Mi consigli un piatto di carne?', context)
        self.assertIn('Beef Burger', reply)
        self.assertNotIn('alternative vegetariane', reply)
        self.assertEqual(context['menu_topic'], 'menu')
        self.assertEqual(context['preferences'], ['vegetariano'])

    def test_pollo_returns_only_dishes_with_pollo(self):
        self.assertEqual(
            self.filtered_names('Consigliami un piatto con pollo'),
            {'Spiedini di pollo'},
        )

    def test_pesce_returns_only_fish_dishes(self):
        self.assertEqual(
            self.filtered_names('Consigliami un piatto di pesce'),
            {'Salmon Roll', 'Tuna Tataki', 'Calamari speziati'},
        )

    def test_salmone_returns_only_dishes_with_salmone(self):
        self.assertEqual(
            self.filtered_names('Vorrei un piatto con salmone'),
            {'Salmon Roll'},
        )

    def test_vegetariano_excludes_meat_and_fish_dishes(self):
        reply, _ = self.ask('Consigliami un piatto vegetariano')
        self.assertIn('Poke vegetariana', reply)
        self.assertNotIn('Beef Burger', reply)

    def test_analcolico_returns_only_alcohol_free_drinks(self):
        reply, context = self.ask('Consigliami un analcolico', {'menu_topic': 'menu'})
        self.assertIn('Virgin Mango', reply)
        self.assertTrue(context['alcohol_free'])
        self.assertEqual(context['menu_topic'], 'cocktail')

    def test_cocktail_with_rum_overrides_old_alcohol_free_filter(self):
        context = {
            'menu_topic': 'cocktail',
            'alcohol_free': True,
            'active_menu_request': {'category': 'cocktail', 'alcohol_free': True},
        }
        reply, context = self.ask('Consigliami un cocktail con rum', context)
        self.assertIn('Rum Punch', reply)
        self.assertNotIn('Virgin Mango', reply)
        self.assertIn('Un drink da vero pirata, Capitano!', reply)
        self.assertNotIn('Una proposta scelta tra quelle disponibili.', reply)
        self.assertFalse(context['alcohol_free'])

    def test_niente_pesce_excludes_every_fish_dish(self):
        names = self.filtered_names('Consigliami un piatto, niente pesce')
        self.assertTrue(names)
        self.assertTrue(names.isdisjoint({'Salmon Roll', 'Tuna Tataki', 'Calamari speziati'}))

    def test_senza_pollo_excludes_every_chicken_dish(self):
        names = self.filtered_names('Consigliami un piatto senza pollo')
        self.assertTrue(names)
        self.assertNotIn('Spiedini di pollo', names)

    def test_qualcos_altro_keeps_category_and_changes_recommendation(self):
        context = {}
        first, context = self.ask('Consigliami un piatto di carne', context)
        second, context = self.ask("Qualcos'altro?", context)
        self.assertIn('Beef Burger', first)
        self.assertIn('Spiedini di pollo', second)
        self.assertEqual(context['menu_topic'], 'menu')

    def test_exclusions_are_not_saved_as_dietary_preferences(self):
        self.assertEqual(dietary_preferences('niente pesce e senza pollo'), [])

    def test_current_cocktail_intent_overrides_old_event_context(self):
        token = _serializer().dumps({
            'step': 'assistente',
            'context': {'intent': 'event'},
        })
        with patch('automatic_chat.get_menu_data', return_value=self.menu):
            result = answer_chat('Consigliami un cocktail con rum', token)
        self.assertIn('Rum Punch', result['reply'])
        state = _serializer().loads(result['session_token'])
        self.assertEqual(state['context']['intent'], 'cocktail')


if __name__ == '__main__':
    unittest.main()
