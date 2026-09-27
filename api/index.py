import os
import time
import hmac
import asyncio
import logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import bookings
import email_sender
from automatic_chat import answer_message
from menu_data import MAKAI_DATA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("makai")


# ---------------------------------------------------------------------------
# Promemoria via email: ogni minuto controlla le prenotazioni a <= 4 ore
# ---------------------------------------------------------------------------
_last_purge = 0.0


def process_reminders():
    global _last_purge
    # pulizia: elimina le prenotazioni vecchie (al massimo una volta all'ora)
    if time.time() - _last_purge > 3600:
        _last_purge = time.time()
        try:
            n = bookings.purge_old_bookings()
            if n:
                logger.info("Eliminate %s prenotazioni vecchie", n)
        except Exception:
            logger.exception("Errore nella pulizia delle prenotazioni")

    if not email_sender.is_configured():
        return
    for b in bookings.due_reminders():
        if not bookings.claim_reminder(b["id"]):
            continue  # già preso in carico da un altro worker
        ok = email_sender.send_reminder(
            b["id"], b["email"], b["name"], b["booking_date"], b["booking_time"], b["party_size"]
        )
        bookings.finish_reminder(b["id"], ok)


async def reminder_loop():
    while True:
        try:
            await asyncio.to_thread(process_reminders)
        except Exception:
            logger.exception("Errore nel ciclo promemoria")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if bookings.DATABASE_URL:
        bookings.init_db()
    else:
        logger.warning("Supabase non configurato: prenotazioni e promemoria disattivati.")
    if not email_sender.is_configured():
        logger.warning("Email (SMTP) non configurata: i promemoria NON verranno inviati.")
    task = asyncio.create_task(reminder_loop()) if bookings.DATABASE_URL else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Makai Grand Line API", lifespan=lifespan)

# CORS: solo i domini autorizzati (imposta ALLOWED_ORIGINS in produzione)
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

# ---------------------------------------------------------------------------
# Rate limit semplice per IP (in memoria)
# ---------------------------------------------------------------------------
RATE_LIMIT = 10
RATE_WINDOW = 60
_hits = defaultdict(deque)


def check_rate_limit(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    now = time.time()
    hits = _hits[ip]
    while hits and now - hits[0] > RATE_WINDOW:
        hits.popleft()
    if len(hits) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Troppe richieste, capitano! Riprova tra un minuto.",
        )
    hits.append(now)


# ---------------------------------------------------------------------------
# Modelli e endpoint
# ---------------------------------------------------------------------------
class HistoryItem(BaseModel):
    sender: Literal["user", "bot"]
    text: str = Field(max_length=1000)


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: List[HistoryItem] = Field(default_factory=list, max_length=10)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "project": "Makai Grand Line Backend"}


@app.get("/api/menu")
async def get_menu():
    return MAKAI_DATA


@app.post("/api/chat")
def automatic_chat(body: ChatMessage, request: Request):
    check_rate_limit(request)
    return {"reply": answer_message(body.message)}


# ---------------------------------------------------------------------------
# Agenda per il gestore (protetta da chiave: header X-Admin-Key)
# ---------------------------------------------------------------------------
ADMIN_KEY = os.environ.get("ADMIN_API_KEY")


def require_admin(x_admin_key: Optional[str]):
    if not ADMIN_KEY:
        raise HTTPException(status_code=503, detail="Admin non configurato.")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(status_code=401, detail="Non autorizzato.")


@app.get("/api/admin/bookings")
def admin_list(date: Optional[str] = None, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    day = date or bookings.now_local().strftime("%Y-%m-%d")
    return {"date": day, "bookings": bookings.list_day(day)}


@app.post("/api/admin/bookings/{booking_id}/cancel")
def admin_cancel(booking_id: int, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    if not bookings.admin_cancel(booking_id):
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Cron esterno gratuito (es. cron-job.org, ogni minuto): utile se l'hosting
# gratuito si "addormenta". Header richiesto: X-Cron-Key = CRON_SECRET
# ---------------------------------------------------------------------------
CRON_SECRET = os.environ.get("CRON_SECRET")


@app.get("/api/cron/reminders")
def cron_reminders(x_cron_key: Optional[str] = Header(default=None)):
    if not CRON_SECRET:
        raise HTTPException(status_code=503, detail="Cron non configurato.")
    if not x_cron_key or not hmac.compare_digest(x_cron_key, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Non autorizzato.")
    process_reminders()
    return {"ok": True}
