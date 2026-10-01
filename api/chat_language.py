"""Comprensione locale: sinonimi e refusi conservativi, mai sui dati di contatto."""
import re
import unicodedata
from difflib import get_close_matches

VOCABULARY = (
    'prenotare', 'prenotazione', 'prenota', 'prenotiamo', 'tavolo', 'disponibilita',
    'compleanno', 'laurea', 'festa', 'feste', 'evento', 'eventi', 'pacchetto', 'buffet',
    'aperitivo', 'apericena', 'prosecco', 'cocktail', 'analcolico', 'vegetariano',
    'vegetariana', 'vegetariane', 'glutine', 'sushi', 'pesce', 'consigli', 'mangiare',
    'informazioni', 'persone', 'bambini', 'variazioni', 'modifiche', 'sabato', 'domenica', 'venerdi', 'giovedi', 'mercoledi',
    'martedi', 'lunedi', 'domani', 'locale', 'pigneto', 'contatti', 'indirizzo',
    'orari', 'social', 'instagram', 'facebook', 'metro', 'mezzi', 'trasporti',
    'carne', 'manzo', 'pollo', 'maiale', 'bacon', 'pancetta', 'salsiccia',
    'hamburger', 'beef', 'chicken', 'salmone', 'tonno', 'gambero', 'gamberi',
    'gamberone', 'gamberoni', 'polpo', 'calamaro', 'calamari', 'orata', 'spigola',
)
NUMBERS = {'uno': 1, 'una': 1, 'due': 2, 'tre': 3, 'quattro': 4, 'cinque': 5,
           'sei': 6, 'sette': 7, 'otto': 8, 'nove': 9, 'dieci': 10, 'venti': 20,
           'trenta': 30, 'quaranta': 40}


def understand(message):
    text = unicodedata.normalize('NFKD', message.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    def correct(match):
        word = match[0]
        if word in VOCABULARY or len(word) < 5:
            return word
        candidates = get_close_matches(word, VOCABULARY, n=1, cutoff=0.86)
        return candidates[0] if candidates else word
    return re.sub(r'\b[a-z]+\b', correct, text)


def people_count(text, bare=False):
    text = understand(text)
    words = '|'.join(NUMBERS)
    number = rf'(\d{{1,3}}|{words})'
    patterns = [rf'\b{number}\s+(?:persone|persona|ospiti|amici)\b',
                rf'\b(?:siamo(?:\s+in)?|saremo(?:\s+in)?|per|in)\s+{number}\b(?![/.:\d])']
    if bare:
        patterns.append(rf'^\s*{number}\s*[.!]?\s*$')
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match[1]
            return int(value) if value.isdigit() else NUMBERS[value]
    return None


def intent(text):
    text = understand(text)
    if re.search(r'\b(compleann\w*|fest[ae]|laure\w*|event\w*|aziendale|gruppo|pacchett\w*|buffet|apericena|aperitivo|dopo\s*cena|preventivo)\b', text):
        return 'event'
    if re.search(r'\b(prenot\w*|riserv\w*)\b', text):
        return 'booking'
    if re.search(r'\b(tavol\w*|posto|posti|disponibil\w*|liberi|libero)\b', text):
        return 'availability'
    if re.search(r'\b(info|informazion\w*|locale|chi siete|parlami|raccontami|come stai|come va|tutto bene|orari|orario|aprite|aperti|chiudete|indirizzo|dove siete|dove si trova|come arrivo|mappa|metro|mezzi|trasport\w*|parcheggi\w*|contatt\w*|telefono|email|social|instagram|facebook|ciao|salve|buonasera|buongiorno|grazie|arrivederci)\b', text):
        return 'info'
    if re.search(r'\b(cocktail\w*|drink\w*|bere|rum|analcolic\w*|senza alcol)\b', text):
        return 'cocktail'
    if re.search(r'\b(menu|mangiar\w*|piatt\w*|cibo|sushi|poke|carne|manzo|pollo|maiale|bacon|pancetta|salsiccia|hamburger|beef|chicken|pesce|salmone|tonno|gamber\w*|polp\w*|calamar\w*|orata|spigola|vegetarian\w*|vegan\w*|glutine|celiac\w*|allerg\w*|dolc[ei]|dessert|bambin\w*|variazion\w*|modific\w*)\b', text):
        return 'menu'
    return None


def dietary_preferences(text):
    text = understand(text)
    preferences = []
    for name, pattern in [('vegetariano', r'\bvegetarian\w*'),
                          ('vegano', r'\bvegan\w*'),
                          ('senza glutine', r'\bglutine\b|\bceliac\w*'),
                          ('allergie', r'\ballerg\w*|\bintoller\w*')]:
        if re.search(pattern, text):
            preferences.append(name)
    if re.search(r'\bnon\s+(?:sono|siamo)\s+vegetarian\w*', text):
        preferences = [name for name in preferences if name != 'vegetariano']
    if re.search(r'\bnon\s+(?:sono|siamo)\s+vegan\w*', text):
        preferences = [name for name in preferences if name != 'vegano']
    return preferences
