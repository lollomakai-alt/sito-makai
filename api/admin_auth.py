"""Login dell'unico gestore e sessione firmata, senza credenziali nel browser."""
import hashlib
import hmac
import os
import time
from collections import deque
from threading import Lock

from fastapi import APIRouter, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel, Field

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or os.environ.get("ADMIN_API_KEY", "")
SESSION_SECRET = os.environ.get("ADMIN_SESSION_SECRET", "")
COOKIE_SECURE = bool(os.environ.get("VERCEL")) or os.environ.get("ADMIN_COOKIE_SECURE", "true").lower() != "false"
COOKIE_NAME = "makai_admin_session"
SESSION_SECONDS = 8 * 60 * 60
LOGIN_WINDOW = 60
LOGIN_LIMIT = 10
_login_attempts = deque()
_login_lock = Lock()
router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1000)


def serializer():
    if not ADMIN_PASSWORD or len(SESSION_SECRET) < 32:
        raise HTTPException(status_code=503, detail="Accesso amministratore non configurato.")
    return URLSafeTimedSerializer(SESSION_SECRET, salt="makai-admin-session-v1")


def credential_version():
    # Cambiare utente o password invalida le sessioni precedenti.
    return hmac.new(SESSION_SECRET.encode(), (ADMIN_USERNAME + "\0" + ADMIN_PASSWORD).encode(), hashlib.sha256).hexdigest()


def require_browser_action(request: Request):
    # Un form esterno non può impostare questo header; CORS non lo consente.
    if request.headers.get("X-Admin-Request") != "1" or request.headers.get("Sec-Fetch-Site") == "cross-site":
        raise HTTPException(status_code=403, detail="Richiesta non consentita.")
    origin = request.headers.get("origin")
    trusted_origins = {str(request.base_url).rstrip("/")}
    trusted_origins.update(value.strip().rstrip("/") for value in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",") if value.strip() and value.strip() != "*")
    if origin and origin.rstrip("/") not in trusted_origins:
        raise HTTPException(status_code=403, detail="Origine non consentita.")


def require_admin(request: Request):
    signer = serializer()
    token = request.cookies.get(COOKIE_NAME, "")
    try:
        session = signer.loads(token, max_age=SESSION_SECONDS)
        if not isinstance(session, dict) or session.get("username") != ADMIN_USERNAME:
            raise BadSignature("Invalid account")
        version = session.get("version")
        if not isinstance(version, str) or not hmac.compare_digest(version, credential_version()):
            raise BadSignature("Credentials changed")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Accedi per consultare l’agenda.") from None
    return session


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response):
    require_browser_action(request)
    signer = serializer()
    now = time.monotonic()
    # Limite per l'unico account, non aggirabile cambiando l'header dell'IP.
    with _login_lock:
        while _login_attempts and now - _login_attempts[0] >= LOGIN_WINDOW:
            _login_attempts.popleft()
        if len(_login_attempts) >= LOGIN_LIMIT:
            raise HTTPException(status_code=429, detail="Troppi tentativi. Riprova tra un minuto.", headers={"Retry-After": "60"})
        _login_attempts.append(now)
    valid_user = hmac.compare_digest(body.username.encode(), ADMIN_USERNAME.encode())
    valid_password = hmac.compare_digest(body.password.encode(), ADMIN_PASSWORD.encode())
    if not (valid_user and valid_password):
        raise HTTPException(status_code=401, detail="Nome utente o password non corretti.")
    token = signer.dumps({"username": ADMIN_USERNAME, "version": credential_version()})
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=COOKIE_SECURE, samesite="strict", path="/api/admin")
    return {"username": ADMIN_USERNAME}


@router.get("/session")
def session(request: Request):
    account = require_admin(request)
    return {"username": account["username"]}


@router.post("/logout")
def logout(request: Request, response: Response):
    require_browser_action(request)
    response.delete_cookie(COOKIE_NAME, path="/api/admin", httponly=True,
                           secure=COOKIE_SECURE, samesite="strict")
    return {"ok": True}
