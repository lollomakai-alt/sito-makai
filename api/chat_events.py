"""Pacchetti comunicati dal locale. Solo stime, nessuna scrittura Bookings."""
import re
from chat_language import people_count

PACKAGES = {
    'aperitivo': (15, '1 drink e snack: platano, patate dolci e nuvole di drago'),
    'apericena': (25, '1 drink, snack, involtini primavera, gyoza, sushi e tagliolino Thai oppure riso saltato; opzioni carne, pesce o vegetariano'),
    'drink + torta': (15, '1 drink e torta: Cheesecake al Frutto del Diavolo oppure Tiki Misù'),
    'drink + snack': (15, '1 drink e snack'),
    'drink + prosecco': (15, '1 drink e prosecco'),
}


EVENT_CHOICE = (
    'Per consigliarti la formula più adatta, pensavate a:\n'
    '• un aperitivo\n'
    '• una cena / apericena\n'
    '• un dopocena\n\n'
    'Dimmi quale preferite e ti spiego le opzioni disponibili.'
)


def _category(text):
    if re.search(r'\bdopo\s*cena\b|\bdopocena\b', text):
        return 'dopo cena'
    if re.search(r'\bapericena\b|\bcena\b', text):
        return 'apericena'
    if re.search(r'\baperitivo\b', text):
        return 'aperitivo'
    return None


def _package(text, category):
    if category == 'aperitivo':
        return 'aperitivo'
    if category == 'apericena':
        return 'apericena'
    if category == 'dopo cena' or 'drink' in text:
        variant = next((value for value in ('torta', 'snack', 'prosecco') if value in text), None)
        return 'drink + ' + variant if variant else None
    return None


def _details(package):
    if package == 'aperitivo':
        return (
            'Per l’aperitivo abbiamo una formula da €15 a persona che comprende:\n'
            '• 1 drink a persona\n'
            '• snack da condividere con platano, patate dolci e nuvole di drago\n\n'
            'È una formula semplice e informale, adatta se volete bere qualcosa insieme senza fare una cena completa.'
        )
    if package == 'apericena':
        return (
            'Per cena ti consiglierei la nostra Apericena da €25 a persona.\n\n'
            'Comprende:\n'
            '• 1 drink a persona\n'
            '• snack\n'
            '• involtini primavera\n'
            '• gyoza\n'
            '• sushi\n'
            '• un primo a scelta tra tagliolino Thai e riso saltato\n\n'
            'Possiamo organizzare la proposta con opzioni di carne, pesce o vegetariane.\n\n'
            'Se volete aggiungere anche la torta, è disponibile come extra a €3 a persona.'
        )
    descriptions = {
        'drink + torta': '• Drink + torta\nUn drink a persona con Cheesecake al Frutto del Diavolo oppure Tiki Misù.',
        'drink + snack': '• Drink + snack\nUn drink a persona accompagnato dai nostri snack.',
        'drink + prosecco': '• Drink + prosecco\nUna formula pensata per brindare insieme.',
    }
    return descriptions.get(package, '')


def _after_dinner_choices():
    return (
        'Per il dopocena abbiamo diverse formule da €15 a persona.\n\n'
        'Potete scegliere tra:\n\n'
        '• Drink + torta\nUn drink a persona con Cheesecake al Frutto del Diavolo oppure Tiki Misù.\n\n'
        '• Drink + snack\nUn drink a persona accompagnato dai nostri snack.\n\n'
        '• Drink + prosecco\nUna formula pensata per brindare insieme.\n\n'
        'Per le feste possiamo inoltre aggiungere bottiglie di prosecco a €20.\n\n'
        'Quale di queste formule vi interessa di più?'
    )


def answer_event(text, context, phone):
    event = context.setdefault('event', {})
    waiting_bottles = event.get('awaiting_bottles', False)
    count = people_count(text, bare=not waiting_bottles)
    if count is not None:
        if count < 1:
            return 'Per quante persone vuoi organizzare la festa? Indica almeno una persona.'
        event['people'] = count

    category = _category(text)
    if category:
        event['category'] = category
    selected = _package(text, category or event.get('category'))
    if selected and selected != event.get('package'):
        event.update(package=selected, cake=False, bottles=0)
    selected = event.get('package')

    if re.search(r'\b(?:senza|togli|niente)\s+(?:la\s+)?torta', text):
        event['cake'] = False
    elif 'torta' in text and selected != 'drink + torta':
        event['cake'] = True
    if re.search(r'\b(?:senza|togli|niente)\s+(?:il\s+)?prosecco', text):
        event['bottles'] = 0
        event.pop('awaiting_bottles', None)

    bottle = re.search(r'\b(\d{1,2}|una|un|due|tre)\s+bottigli[ae](?:(?:\s+di)?\s+prosecco)?\b', text)
    if waiting_bottles and not bottle:
        bottle = re.fullmatch(r'\s*(\d{1,2}|una|un|due|tre)\s*[.!]?\s*', text)
    if bottle:
        event.pop('awaiting_bottles', None)
        quantities = {'una': 1, 'un': 1, 'due': 2, 'tre': 3}
        event['bottles'] = quantities[bottle[1]] if bottle[1] in quantities else int(bottle[1])
    elif 'prosecco' in text and selected != 'drink + prosecco' and not re.search(r'senza|togli|niente', text):
        event['awaiting_bottles'] = True

    count = event.get('people')
    if not selected:
        if event.get('category') == 'dopo cena':
            return _after_dinner_choices()
        return EVENT_CHOICE
    if not count:
        return _details(selected) + '\n\nQuante persone sareste?'
    if count > 40:
        return (f'Per {count} persone la richiesta va valutata direttamente con il locale al {phone}. '
                'Non registro automaticamente gli eventi; formula, preventivo e conferma vanno concordati in struttura.')

    lines = [_details(selected)]
    if count > 30:
        lines.append(f'Per {count} persone è possibile la formula in piedi con buffet.')
    else:
        lines.append(f'Per {count} persone è possibile organizzare l’evento con posti a sedere.')
    price = PACKAGES[selected][0]
    total = count * price
    lines.append(f'{count} × €{price} = €{total}.')
    if event.get('cake'):
        total += count * 3
        lines.append(f'Torta aggiuntiva: {count} × €3 = €{count * 3}.')
    bottles = event.get('bottles', 0)
    if bottles:
        total += bottles * 20
        lines.append(f'Bottiglie di prosecco: {bottles} × €20 = €{bottles * 20}.')
    lines.append(f'Totale indicativo: €{total} — stima non definitiva.')
    lines.append(f'La conferma dell’evento e il preventivo definitivo vanno concordati direttamente in struttura: {phone}.')
    if event.get('awaiting_bottles') and not bottle:
        lines.append('Quante bottiglie di prosecco vuoi aggiungere?')
    return '\n'.join(lines)
