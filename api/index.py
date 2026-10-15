import os
import re
import sys
import time
import asyncio
import logging
from pathlib import Path
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from typing import List, Literal, Optional, Union
from uuid import UUID

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
from bookings.online import create_online_booking, PRIVACY_VERSION
from bookings.customer import customer_action
from bookings.dates import _slots
from admin_auth import router as auth_router, require_admin, require_browser_action, require_agenda_gateway
from booking_communications import router as communications_router, send_new_online_booking_email, send_customer_action_email
from booking_push import send_new_online_booking_push
from maintenance_mode import router as maintenance_router, public_status, MaintenanceActive
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
app.include_router(maintenance_router)


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
    phone: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=120)
    date: str = Field(min_length=10, max_length=10)
    time: str = Field(min_length=5, max_length=5)
    party_size: int = Field(strict=True, ge=1)
    notes: str = Field(default="", max_length=300)


class OnlineBookingBody(AdminBookingBody):
    phone: str = Field(min_length=8, max_length=30)
    party_size: int = Field(strict=True, ge=1, le=MAX_PARTY_SIZE)
    model_config = ConfigDict(extra="forbid")
    privacy: StrictBool
    marketing: StrictBool = False
    request_id: str = Field(min_length=36, max_length=36)
    booking_type: Literal["normale", "dopocena"] = "normale"


class CustomerActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=43,max_length=43)

class CustomerRequestBody(CustomerActionBody):
    request_type: Literal["data","ora","persone","cancellazione","note"]
    requested_value: object = None
    operation_id: UUID

@app.post("/api/booking-management/{action}")
def manage_customer_booking(action: Literal["view","reconfirm","request"], body: Union[CustomerRequestBody, CustomerActionBody], request: Request, response: Response):
    check_rate_limit(request)
    response.headers["Cache-Control"] = "no-store"
    if action == "request" and not isinstance(body,CustomerRequestBody):
        raise HTTPException(status_code=422,detail="Richiesta incompleta.")
    try:
        result = customer_action(body.token, action, getattr(body,"request_type",None),
                                 getattr(body,"requested_value",None), getattr(body,"operation_id",None))
        booking_id = result.pop('_booking_id', None)
        communication_id = result.pop('_communication_id', None)
        if booking_id and communication_id:
            send_customer_action_email(booking_id, communication_id)
        if result.get('outcome') == 'pending':
            response.status_code = 202
        return result
    except ValueError:
        raise HTTPException(status_code=404,detail="Collegamento non valido o scaduto.") from None
    except Exception as error:
        if getattr(error,'sqlstate','') in ('P0002','40001','22023','P0001'):
            raise HTTPException(status_code=409,detail="Richiesta non disponibile. Aggiorna la pagina o contatta il locale.") from None
        raise HTTPException(status_code=503,detail="Servizio momentaneamente non disponibile.") from None


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
        elif result['status'] == 'pending':
            response.status_code = 202
        elif result['status'] == 'confirmed':
            # The booking transaction has committed; push failures must not undo it.
            try:
                send_new_online_booking_push(result['booking_id'])
            except Exception:
                logger.warning('Notifica push automatica non confermata; prenotazione salvata.')
            if body.email.strip():
                # Email outcome must never change the successful booking response.
                try:
                    send_new_online_booking_email(result['booking_id'])
                except Exception:
                    logger.warning('Conferma email automatica non confermata; prenotazione salvata.')
        return {key:value for key,value in result.items() if key != 'booking_id'}
    except MaintenanceActive:
        raise HTTPException(status_code=503, detail="Le prenotazioni online sono temporaneamente sospese.",
                            headers={"Retry-After": "300"}) from None
    except HTTPException:
        raise
    except Exception as error:
        # Never return raw SQL/contacts or credentials to public clients.
        if getattr(error, 'sqlstate', '') in {'P0001','23514','23505','22023'}:
            raise HTTPException(status_code=409, detail="Disponibilità cambiata. Aggiorna il calendario o contatta il locale.") from None
        logger.warning("Salvataggio prenotazione online non disponibile.")
        raise HTTPException(status_code=503, detail="Salvataggio non confermato. Riprova con gli stessi dati.") from None


@app.get("/api/site-maintenance")
def site_maintenance_status(response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        return public_status()
    except Exception:
        raise HTTPException(status_code=503, detail="Stato manutenzione non disponibile.") from None


@app.get("/api/booking-settings")
def booking_settings():
    return {"max_party_size": MAX_PARTY_SIZE, "phone": LOCAL_PHONE, "max_advance_days": MAX_ADVANCE_DAYS, "times": _slots(), "services": {"normale": _slots(), "dopocena": ["22:30","23:00","23:30","00:00"]}, "kitchen_close": "23:30", "venue_close": {"default":"01:00","saturday":"02:00"}, "privacy_version": PRIVACY_VERSION}


@app.get("/api/booking-availability")
def public_booking_availability(request: Request, response: Response,
                                month: str, party_size: int = Query(ge=1, le=MAX_PARTY_SIZE),
                                booking_type: Literal["normale", "dopocena"] = "normale", booking_time: Optional[str] = None):
    check_rate_limit(request)
    response.headers["Cache-Control"] = "no-store"
    try:
        if public_status()["active"]:
            raise MaintenanceActive()
        return month_availability(month, party_size, booking_type, booking_time)
    except MaintenanceActive:
        raise HTTPException(status_code=503, detail="Le prenotazioni online sono temporaneamente sospese.",
                            headers={"Retry-After": "300"}) from None
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
    except Exception as error:
        category = type(error).__name__
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", category):
            category = "Exception"
        sqlstate = getattr(error, "sqlstate", None)
        if not isinstance(sqlstate, str) or not re.fullmatch(r"[0-9A-Z]{5}", sqlstate):
            sqlstate = "unavailable"
        logger.warning(
            "Creazione manuale della prenotazione non disponibile: "
            "category=%s sqlstate=%s.",
            category,
            sqlstate,
        )
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
