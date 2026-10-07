import os
import re
import sys
import time
import asyncio
import logging
from pathlib import Path
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, StrictBool
from dotenv import load_dotenv

API_DIR = Path(__file__).resolve().parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

load_dotenv(API_DIR.parent / ".env")

import bookings
from bookings.calendar_summary import month_summary
from bookings.public_availability import month_availability
from bookings.online import create_online_booking
from bookings.dates import _slots
from admin_auth import router as auth_router, require_admin, require_browser_action, require_agenda_gateway
from booking_communications import router as communications_router, send_new_online_booking_email
from bookings.maintenance import cleanup_loop
from automatic_chat import answer_chat
from config import MAX_PARTY_SIZE, LOCAL_PHONE, MAX_ADVANCE_DAYS
from origins import allowed_origins
from menu_data import get_menu_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("makai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_ready = False
    if bookings.DATABASE_URL:
        try:
            bookings.init_db()
            database_ready = True
        except Exception:
            logger.warning("Database prenotazioni non raggiungibile: agenda disattivata.")
    else:
        logger.warning("Supabase non configurato: prenotazioni disattivate.")
    cleanup_enabled = os.environ.get("BOOKINGS_AUTO_CLEANUP", "false").lower() == "true"
    task = asyncio.create_task(cleanup_loop()) if database_ready and cleanup_enabled else None
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="Makai Grand Line API", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(communications_router)


@app.middleware("http")
async def private_admin_responses(request: Request, call_next):
    if request.url.path == "/api/admin" or request.url.path.startswith("/api/admin/"):
        try:
            require_agenda_gateway(request)
        except HTTPException as error:
            return JSONResponse(status_code=error.status_code, content={"detail": error.detail},
                                headers={"Cache-Control": "no-store", "Vary": "Authorization"})
    response = await call_next(request)
    if request.url.path.startswith("/api/admin/") or request.url.path == "/api/chat":
        response.headers["Cache-Control"] = "no-store"
        response.headers["Vary"] = "Authorization, Cookie"
    return response


# CORS: solo i domini autorizzati (imposta ALLOWED_ORIGINS in produzione)
ALLOWED_ORIGINS = allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# Rate limit semplice per IP (in memoria)
# ---------------------------------------------------------------------------
RATE_LIMIT = 30
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
    session_token: Optional[str] = Field(default=None, max_length=8192)


class AdminBookingBody(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    phone: str = Field(min_length=8, max_length=30)
    email: str = Field(default="", max_length=120)
    date: str = Field(min_length=10, max_length=10)
    time: str = Field(min_length=5, max_length=5)
    party_size: int = Field(strict=True, ge=1, le=MAX_PARTY_SIZE)
    notes: str = Field(default="", max_length=300)


class OnlineBookingBody(AdminBookingBody):
    model_config = ConfigDict(extra="forbid")
    privacy: StrictBool
    marketing: StrictBool = False
    request_id: str = Field(min_length=36, max_length=36)


class MarketingConsentBody(BaseModel):
    channel: Literal["whatsapp", "telefono", "email"]
    response_text: str = Field(min_length=1, max_length=200)


@app.get("/", include_in_schema=False)
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "project": "Makai Grand Line Backend"}


@app.post("/api/bookings", status_code=201)
def public_create_booking(body: OnlineBookingBody, request: Request, response: Response):
    check_rate_limit(request)
    response.headers["Cache-Control"] = "no-store"
    try:
        result = create_online_booking(**body.model_dump())
        if not result["ok"]:
            raise HTTPException(status_code=409, detail=result["error"])
        if result["replayed"]:
            response.status_code = 200
        elif result['status'] == 'confirmed' and body.email.strip():
            # create_online_booking has returned only after its transaction commits.
            # Email outcome must never change the successful booking response.
            try:
                send_new_online_booking_email(result['booking_id'])
            except Exception:
                logger.warning('Conferma email automatica non confermata; prenotazione salvata.')
        return result
    except HTTPException:
        raise
    except Exception as error:
        # Never return raw SQL/contacts or credentials to public clients.
        if getattr(error, 'sqlstate', '') in {'P0001','23514','23505','22023'}:
            raise HTTPException(status_code=409, detail="Disponibilità cambiata. Aggiorna il calendario o contatta il locale.") from None
        logger.warning("Salvataggio prenotazione online non disponibile.")
        raise HTTPException(status_code=503, detail="Salvataggio non confermato. Riprova con gli stessi dati.") from None


@app.get("/api/booking-settings")
def booking_settings():
    return {"max_party_size": MAX_PARTY_SIZE, "phone": LOCAL_PHONE, "max_advance_days": MAX_ADVANCE_DAYS, "times": _slots(), "privacy_version": "2026-10-04-online-v1"}


@app.get("/api/booking-availability")
def public_booking_availability(request: Request, response: Response,
                                month: str, party_size: int = Query(ge=1, le=MAX_PARTY_SIZE)):
    check_rate_limit(request)
    response.headers["Cache-Control"] = "no-store"
    try:
        return month_availability(month, party_size)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except Exception as error:
        detail = str(error)
        database_url = os.environ.get("DATABASE_URL", "")
        if database_url:
            detail = detail.replace(database_url, "[DATABASE_URL]")
        detail = re.sub(r"(?i)postgres(?:ql)?://[^\s'\"<>]+", "[DATABASE_URL]", detail)
        detail = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", detail)
        detail = re.sub(
            r"(?i)\b(password|passfile|token|secret|api[_-]?key)\s*[=:]\s*[^\s,;]+",
            r"\1=[REDACTED]",
            detail,
        )
        logger.warning(
            "Disponibilità pubblica momentaneamente non disponibile: tipo=%s sqlstate=%s dettaglio=%s",
            type(error).__name__,
            getattr(error, "sqlstate", None),
            detail,
        )
        raise HTTPException(status_code=503, detail="Disponibilità non verificabile. Riprova più tardi.") from None


@app.get("/api/menu")
def get_menu():
    try:
        return get_menu_data()
    except RuntimeError as error:
        logger.error("Menu Supabase non disponibile: %s", error)
        raise HTTPException(
            status_code=503,
            detail="Menu momentaneamente non disponibile.",
        ) from error
    except Exception as error:
        logger.exception("Errore durante la lettura del menu da Supabase")
        raise HTTPException(
            status_code=503,
            detail="Menu momentaneamente non disponibile.",
        ) from error


@app.post("/api/chat")
def automatic_chat(body: ChatMessage, request: Request):
    check_rate_limit(request)
    return answer_chat(
        body.message,
        body.session_token,
    )


# ---------------------------------------------------------------------------
# Agenda per il gestore (sessione richiesta anche per le chiamate API dirette)
# ---------------------------------------------------------------------------
@app.get("/api/admin/bookings")
def admin_list(request: Request, response: Response, date: Optional[str] = None):
    require_admin(request)
    response.headers["Cache-Control"] = "no-store"
    day = date or bookings.now_local().strftime("%Y-%m-%d")
    try:
        rows = bookings.list_day(day)
    except Exception:
        logger.warning("Agenda non disponibile: controllare connessione e tabella prenotazioni.")
        raise HTTPException(status_code=503, detail="Agenda non disponibile: controlla il database prenotazioni.") from None
    return {"date": day, "bookings": rows}


@app.post("/api/admin/bookings")
def admin_create(body: AdminBookingBody, request: Request):
    require_browser_action(request)
    require_admin(request)
    try:
        result = bookings.create_admin_booking(
            name=body.name,
            phone=body.phone,
            email=body.email,
            date=body.date,
            time=body.time,
            party_size=body.party_size,
            notes=body.notes,
        )
    except Exception:
        logger.warning("Creazione manuale della prenotazione non disponibile.")
        raise HTTPException(status_code=503, detail="Prenotazione non salvata: controlla il database.") from None
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error", "Prenotazione non valida."))
    return result


@app.get("/api/admin/bookings/month")
def admin_month(request: Request, month: str):
    require_admin(request)
    try:
        days = month_summary(month)
    except ValueError:
        raise HTTPException(status_code=422, detail="Mese non valido: usa AAAA-MM.") from None
    except Exception:
        logger.warning("Riepilogo mensile non disponibile.")
        raise HTTPException(status_code=503, detail="Calendario non disponibile: controlla il database prenotazioni.") from None
    return {"month": month, "days": days}


@app.post("/api/admin/bookings/{booking_id}/cancel")
def admin_cancel(booking_id: int, request: Request):
    require_browser_action(request)
    require_admin(request)
    if not bookings.admin_cancel(booking_id):
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")
    return {"ok": True}


@app.post("/api/admin/bookings/{booking_id}/marketing-consent")
def admin_marketing_consent(booking_id: int, body: MarketingConsentBody, request: Request):
    require_browser_action(request)
    account = require_admin(request)
    try:
        result = bookings.register_marketing_consent(
            booking_id=booking_id,
            channel=body.channel,
            response_text=body.response_text,
            recorded_by=account["username"],
        )
    except Exception:
        logger.warning("Registrazione del consenso marketing non disponibile.")
        raise HTTPException(status_code=503, detail="Consenso non salvato: controlla il database.") from None
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error", "Consenso non valido."))
    return result


@app.post("/api/admin/bookings/{booking_id}/marketing-consent/revoke")
def admin_revoke_marketing_consent(booking_id: int, request: Request):
    require_browser_action(request)
    account = require_admin(request)
    try:
        revoked = bookings.revoke_marketing_consent(booking_id, account["username"])
    except Exception:
        logger.warning("Revoca del consenso marketing non disponibile.")
        raise HTTPException(status_code=503, detail="Revoca non salvata: controlla il database.") from None
    if not revoked:
        raise HTTPException(status_code=404, detail="Consenso marketing attivo non trovato.")
    return {"ok": True}


@app.post("/api/admin/bookings/{booking_id}/arrived")
def admin_mark_arrived(booking_id: int, request: Request):
    require_browser_action(request)
    require_admin(request)
    try:
        result = bookings.mark_arrived(booking_id)
    except Exception:
        logger.warning("Registrazione dell'arrivo non disponibile.")
        raise HTTPException(status_code=503, detail="Arrivo non salvato: controlla il database.") from None
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error", "Arrivo non valido."))
    return result
