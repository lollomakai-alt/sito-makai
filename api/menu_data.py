import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LOCAL_INFO = {
  "name": "Makai Grand Line Pigneto",
  "address": "Via Braccio da Montone, 3/B, 00100 Roma RM",
  "vibe": "Tiki Cocktail Bar & Ristorante a tema One Piece"
}

CATEGORY_KEYS = {
  "Snack": "snack",
  "Sushi": "sushi",
  "Primi": "primi_starters",
  "Secondi": "secondi_main",
  "Dolci": "dolci",
  "Drinks": "cocktails",
  "Analcolici": "analcolici",
  "Volcanoes": "volcanoes",
}


def _category_key(category: str) -> str:
  if category in CATEGORY_KEYS:
    return CATEGORY_KEYS[category]
  return re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_") or "altro"


def _group_menu_rows(rows):
  menu = {key: [] for key in CATEGORY_KEYS.values()}

  for row in rows:
    category = row["category"]
    key = _category_key(category)
    menu.setdefault(key, []).append({
      "id": row["id"],
      "name_it": row["name"],
      "description_it": row.get("description") or "",
      "name_en": row.get("name_en") or row["name"],
      "description_en": row.get("description_en") or row.get("description") or "",
      "price": float(row["price"]),
      "category": category,
    })

  return {
    "local_info": LOCAL_INFO,
    "menu": menu,
  }


def get_menu_data():
  """Legge dalla Data API Supabase gli elementi del menu disponibili."""
  supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
  publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
  if not supabase_url or not publishable_key:
    raise RuntimeError("Mancano SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY.")

  query = urlencode({
    "select": "id,name,description,name_en,description_en,price,category,is_available",
    "is_available": "eq.true",
    "order": "category.asc,id.asc",
  })
  request = Request(
    f"{supabase_url}/rest/v1/menu_items?{query}",
    headers={
      "apikey": publishable_key,
      "Authorization": f"Bearer {publishable_key}",
      "Accept": "application/json",
    },
  )

  try:
    with urlopen(request, timeout=10) as response:
      rows = json.loads(response.read().decode("utf-8"))
  except HTTPError as error:
    raise RuntimeError(f"Supabase Data API ha risposto {error.code}.") from error
  except (URLError, TimeoutError, json.JSONDecodeError) as error:
    raise RuntimeError("Supabase Data API non raggiungibile.") from error

  return _group_menu_rows(rows)
