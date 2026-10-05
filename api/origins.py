"""Origini esplicite condivise da CORS e controllo delle azioni admin."""
import os

AGENDA_PRODUCTION_ORIGIN = "https://agenda-makai.vercel.app"


def allowed_origins():
    configured = os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )
    origins = [AGENDA_PRODUCTION_ORIGIN]
    origins.extend(value.strip().rstrip("/") for value in configured.split(",")
                   if value.strip() and value.strip().rstrip("/") != "*")
    return list(dict.fromkeys(origins))
