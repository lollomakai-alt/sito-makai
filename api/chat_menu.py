"""Risposte basate solo sul menu disponibile restituito da ``load_menu``."""
import random
import re

from chat_language import dietary_preferences, intent, understand


FOOD = ('snack', 'sushi', 'primi_starters', 'secondi_main', 'dolci')
DRINKS = ('cocktails', 'analcolici', 'volcanoes')
ALCOHOLIC_DRINKS = ('cocktails', 'volcanoes')

MEAT_KEYWORDS = (
    'carne', 'manzo', 'pollo', 'maiale', 'bacon', 'pancetta', 'salsiccia',
    'hamburger', 'beef', 'chicken',
)
FISH_KEYWORDS = (
    'pesce', 'salmone', 'tonno', 'gambero', 'gamberi', 'gamberone', 'gamberoni',
    'mazzancolla', 'mazzancolle', 'polpo', 'polpi', 'polipetto', 'polipetti',
    'calamaro', 'calamari', 'orata', 'spigola', 'branzino', 'merluzzo',
    'baccala', 'acciuga', 'acciughe', 'sardina', 'sardine', 'cozza', 'cozze',
    'vongola', 'vongole', 'granchio', 'surimi', 'anguilla', 'crostacei',
    'molluschi', 'frutti di mare',
)
SPECIFIC_INGREDIENTS = tuple(
    keyword for keyword in MEAT_KEYWORDS + FISH_KEYWORDS
    if keyword not in ('carne', 'pesce')
)
TASTES = ('dolce', 'fruttato', 'tropicale', 'rum', 'fresco', 'secco', 'forte')
COCKTAIL_CLOSERS = (
    'Un drink da vero pirata, Capitano!',
    'Issa il bicchiere: questo è un brindisi da ciurma!',
    'Una rotta perfetta per brindare all’avventura!',
)
FOOD_CLOSERS = (
    'Un piatto da affrontare con appetito da vero pirata!',
    'Un bottino gustoso scelto dalla ciurma!',
    'Preparati all’arrembaggio del piatto, Capitano!',
)


def _keyword_pattern(keywords):
    alternatives = '|'.join(re.escape(keyword) for keyword in sorted(keywords, key=len, reverse=True))
    return rf'\b(?:{alternatives})\b'


SPECIFIC_INGREDIENT_ALTERNATIVES = '|'.join(
    re.escape(keyword) for keyword in sorted(SPECIFIC_INGREDIENTS, key=len, reverse=True)
)
SPECIFIC_INGREDIENT_PATTERN = rf'\b(?:{SPECIFIC_INGREDIENT_ALTERNATIVES})\b'
EXCLUSION_PATTERN = re.compile(
    rf"\b(?:senza|niente|no|non\s+voglio)\s+(?:(?:il|lo|la|i|gli|le|del|dello|della|dei|degli|delle)\s+)?"
    rf"(?P<ingredient>carne|pesce|{SPECIFIC_INGREDIENT_ALTERNATIVES})\b"
)


def _item_text(item):
    return understand(f"{item.get('name_it', '')} {item.get('description_it', '')}")


def _matches_keywords(item, keywords):
    return bool(re.search(_keyword_pattern(keywords), _item_text(item)))


def detect_exclusions(text):
    return tuple(dict.fromkeys(match.group('ingredient') for match in EXCLUSION_PATTERN.finditer(text)))


def _without_exclusions(text):
    return re.sub(r'\s+', ' ', EXCLUSION_PATTERN.sub(' ', text)).strip()


def detect_specific_ingredient(text):
    positive_text = _without_exclusions(text)
    return tuple(dict.fromkeys(re.findall(SPECIFIC_INGREDIENT_PATTERN, positive_text)))


def detect_food_type(text):
    positive_text = _without_exclusions(text)
    if re.search(r'\bcarne\b', positive_text):
        return 'carne'
    if re.search(r'\bpesce\b', positive_text):
        return 'pesce'
    ingredients = detect_specific_ingredient(positive_text)
    has_meat = any(ingredient in MEAT_KEYWORDS for ingredient in ingredients)
    has_fish = any(ingredient in FISH_KEYWORDS for ingredient in ingredients)
    if has_meat and not has_fish:
        return 'carne'
    if has_fish and not has_meat:
        return 'pesce'
    return None


def _detect_category(text, topic, food_type, ingredients, exclusions):
    cocktail_signal = bool(re.search(
        r'\b(cocktail\w*|drink\w*|analcolic\w*|senza alcol|non alcolic\w*|rum)\b',
        text,
    ))
    food_signal = bool(
        food_type or ingredients or exclusions or topic == 'menu' or
        re.search(r'\b(menu|piatt\w*|mangiar\w*|cibo|sushi|poke|dolc[ei]|dessert)\b', text)
    )
    if cocktail_signal and not food_signal:
        return 'cocktail'
    if food_signal:
        return 'menu'
    if topic in ('menu', 'cocktail'):
        return topic
    return None


def build_current_request(text, context):
    """Rappresenta i filtri del messaggio corrente prima di consultare il context."""
    topic = intent(text)
    exclusions = detect_exclusions(text)
    ingredients = detect_specific_ingredient(text)
    food_type = detect_food_type(text)
    category = _detect_category(text, topic, food_type, ingredients, exclusions)
    another = bool(re.search(
        r"\b(?:qualcos(?:['’ ]+)altro|un(?:['’ ]+)?altr[oa]|altr[oa])\b",
        text,
    ))

    alcohol_free = None
    if re.search(r'\b(?:analcolic\w*|senza alcol|non alcolic\w*)\b', text):
        alcohol_free = True
    elif re.search(r'\b(?:con rum|rum|alcolico|alcolici|con alcol)\b', text):
        alcohol_free = False

    tastes = tuple(taste for taste in TASTES if re.search(rf'\b{taste}\b', text))
    subcategory = next(
        (value for value in ('sushi', 'poke', 'dolci', 'dessert') if re.search(rf'\b{value}\b', text)),
        None,
    )
    explicit_category = category is not None
    explicit_filters = bool(food_type or ingredients or exclusions or alcohol_free is not None or tastes or subcategory)

    active = dict(context.get('active_menu_request', {}))
    if not active:
        active = {
            'category': context.get('menu_topic'),
            'alcohol_free': context.get('alcohol_free'),
            'tastes': tuple(context.get('tastes', ())),
        }

    if not explicit_category and not explicit_filters:
        category = active.get('category') or context.get('menu_topic') or 'menu'
        food_type = active.get('food_type')
        ingredients = tuple(active.get('ingredients', ()))
        exclusions = tuple(active.get('exclusions', ()))
        alcohol_free = active.get('alcohol_free')
        tastes = tuple(active.get('tastes', ()))
        subcategory = active.get('subcategory')
    else:
        category = category or ('cocktail' if alcohol_free is not None or tastes else 'menu')

    if category == 'cocktail':
        food_type = None
        ingredients = ()
        exclusions = ()
        subcategory = None
        if explicit_category and alcohol_free is None and not tastes:
            alcohol_free = False
    else:
        alcohol_free = None
        tastes = ()

    current_request = {
        'category': category,
        'food_type': food_type,
        'ingredients': ingredients,
        'exclusions': exclusions,
        'alcohol_free': alcohol_free,
        'tastes': tastes,
        'subcategory': subcategory,
        'dietary_preferences': tuple(dietary_preferences(text)),
        'another': another,
    }

    context['menu_topic'] = category
    context['active_menu_request'] = {
        key: value for key, value in current_request.items()
        if key not in ('dietary_preferences', 'another')
    }
    if category == 'cocktail':
        context['alcohol_free'] = alcohol_free
        context['tastes'] = list(tastes)
    else:
        context.pop('alcohol_free', None)
        context.pop('tastes', None)
    return current_request


def _effective_preferences(context, request):
    persistent = list(context.get('preferences', ()))
    if request['food_type'] or request['ingredients']:
        persistent = [preference for preference in persistent if preference not in ('vegetariano', 'vegano')]
    return tuple(dict.fromkeys(persistent + list(request['dietary_preferences'])))


def _matches_exclusion(item, exclusion):
    if exclusion == 'carne':
        return _matches_keywords(item, MEAT_KEYWORDS)
    if exclusion == 'pesce':
        return _matches_keywords(item, FISH_KEYWORDS)
    return _matches_keywords(item, (exclusion,))


def filter_menu_items(items, request, preferences=()):
    filtered = list(items)
    if 'vegetariano' in preferences:
        filtered = [
            item for item in filtered
            if not _matches_keywords(item, MEAT_KEYWORDS + FISH_KEYWORDS)
        ]

    if request['ingredients']:
        filtered = [item for item in filtered if _matches_keywords(item, request['ingredients'])]
    elif request['food_type'] == 'carne':
        filtered = [item for item in filtered if _matches_keywords(item, MEAT_KEYWORDS)]
    elif request['food_type'] == 'pesce':
        filtered = [item for item in filtered if _matches_keywords(item, FISH_KEYWORDS)]

    subcategory = request.get('subcategory')
    if subcategory in ('dolci', 'dessert'):
        filtered = [item for item in filtered if item.get('category') == 'Dolci']
    elif subcategory:
        filtered = [item for item in filtered if subcategory in _item_text(item)]

    for exclusion in request['exclusions']:
        filtered = [item for item in filtered if not _matches_exclusion(item, exclusion)]
    return filtered


def _recommendation_key(item):
    return str(item.get('id') or item.get('name_it', ''))


def choose_recommendation(items, context):
    last_key = context.get('last_menu_recommendation')
    candidates = [item for item in items if _recommendation_key(item) != last_key]
    if not candidates:
        candidates = list(items)
    selected = random.choice(candidates)
    context['last_menu_recommendation'] = _recommendation_key(selected)
    return selected


def _recommendation_label(request, preferences):
    if request['ingredients']:
        return ', '.join(request['ingredients'])
    if request['food_type']:
        return request['food_type']
    if 'vegetariano' in preferences:
        return 'vegetariano'
    if request['alcohol_free'] is True:
        return 'analcolico'
    if request['tastes']:
        return ', '.join(request['tastes'])
    return None


def _format_recommendation(item, request, preferences):
    label = _recommendation_label(request, preferences)
    lead = f"Seguendo la rotta {label}, " if label else "Dal menu reale, "
    description = item.get('description_it') or ''
    closer = random.choice(
        COCKTAIL_CLOSERS if request['category'] == 'cocktail' else FOOD_CLOSERS
    )
    ingredients = (
        f" Ingredienti indicati in carta: {description}."
        if description else " La carta non riporta una descrizione degli ingredienti."
    )
    return (
        f"{lead}ti suggerisco {item['name_it']} (€{item['price']:.2f})."
        f"{ingredients} {closer}"
    )


def answer_menu(message, context, load_menu, phone):
    text = understand(message)
    current_request = build_current_request(text, context)
    explicit_preferences = current_request['dietary_preferences']

    if 'senza glutine' in explicit_preferences:
        return (f'Possiamo preparare sushi senza glutine e valutare modifiche ai piatti quando possibile. '
                f'Non posso garantire l’assenza di contaminazione: verifica ingredienti e preparazione con il locale al {phone}.')
    if 'allergie' in explicit_preferences or 'vegano' in explicit_preferences:
        return f'Per questa esigenza verifichiamo ingredienti e preparazione direttamente con il locale al {phone}; non posso dedurre la sicurezza dalla sola descrizione del menu.'

    try:
        menu = load_menu()['menu']
    except Exception:
        return f'Non riesco a leggere il menu aggiornato. Riprova tra poco oppure contattaci al {phone}.'

    if re.search(r'\b(?:variazion\w*|modific\w*)\b', text):
        return f'Possiamo valutare variazioni ai piatti quando possibile. Per ingredienti, porzioni e allergie verifica sempre con il locale al {phone}.'
    if re.search(r'\bbambin\w*\b', text):
        return f'Per i più piccoli possiamo valutare i piatti già presenti nel menu e le variazioni possibili. Per porzioni e ingredienti adatti, chiedi conferma al locale al {phone}.'

    category = current_request['category']
    if category == 'cocktail':
        if current_request['alcohol_free'] is True:
            keys = ('analcolici',)
        elif current_request['alcohol_free'] is False:
            keys = ALCOHOLIC_DRINKS
        else:
            keys = DRINKS
    else:
        keys = FOOD
    items = [item for key in keys for item in menu.get(key, [])]

    preferences = _effective_preferences(context, current_request)
    if category == 'menu':
        if 'allergie' in preferences or 'senza glutine' in preferences or 'vegano' in preferences:
            return f'Per rispettare le esigenze alimentari indicate serve verificare ingredienti e preparazione con il locale al {phone}. Non garantisco assenza di contaminazione.'
        items = filter_menu_items(items, current_request, preferences)
    elif current_request['tastes']:
        items = [
            item for item in items
            if any(taste in _item_text(item) for taste in current_request['tastes'])
        ]

    if not items:
        return f'Non trovo proposte disponibili con queste caratteristiche nel menu aggiornato. Per varianti e dettagli contattaci al {phone}.'

    recommend = bool(re.search(
        r"consigl\w*|suggeri\w*|prover\w*|qualcosa|un(?:['’ ]+)?altr[oa]|qualcos(?:['’ ]+)altro|alternativa",
        text,
    ))
    if recommend:
        return _format_recommendation(
            choose_recommendation(items, context),
            current_request,
            preferences,
        )

    ignored = {
        'vorrei', 'consigli', 'consiglio', 'mangiare', 'qualcosa', 'avete', 'posso',
        'sono', 'menu', 'cocktail', 'drink', 'piatti', 'quanto', 'costa', 'prezzo',
        'quale', 'quali', 'buono', 'proponi', 'proposte', 'disponibili', 'carne', 'pesce',
    }
    words = {word for word in re.findall(r'[a-z]+', text) if len(word) >= 4 and word not in ignored}
    ranked = sorted(
        items,
        key=lambda item: (
            sum(2 for word in words if word in understand(item['name_it'])) +
            sum(1 for word in words if word in understand(item.get('description_it', '')))
        ),
        reverse=True,
    )
    lines = [
        f"• {item['name_it']} — €{item['price']:.2f}" +
        (f": {item['description_it']}" if item.get('description_it') else '')
        for item in ranked[:6]
    ]
    heading = 'Dalla carta aggiornata:\n' if category == 'cocktail' else 'Ecco le proposte disponibili:\n'
    return heading + '\n'.join(lines)
