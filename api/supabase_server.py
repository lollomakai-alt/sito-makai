"""Client Supabase dedicato al backend, senza sessioni utente o logging di segreti."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request as URLRequest, build_opener, HTTPRedirectHandler

from fastapi import HTTPException


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SupabaseSendError(HTTPException):
    """Only sanitized transport metadata; never retain provider bodies or credentials."""
    def __init__(self, outcome, error_code):
        super().__init__(status_code=502, detail='Invio email non confermato.')
        self.outcome = outcome
        self.error_code = error_code


class SupabaseServer:
    def __init__(self):
        url = os.environ.get('SUPABASE_URL', '').rstrip('/')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
        try:
            parsed = urlsplit(url)
            valid_url = (parsed.scheme == 'https' and parsed.hostname and not parsed.username
                         and not parsed.password and not parsed.path and not parsed.query
                         and not parsed.fragment and (parsed.port is None or 0 < parsed.port <= 65535))
        except ValueError:
            valid_url = False
        if not valid_url or not key or any(character.isspace() for character in key):
            raise HTTPException(status_code=503, detail='Supabase server non configurato.')
        self._url = url
        self._key = key

    def request(self, method, path, payload=None, sending=False, expect_void=False):
        # Callers supply only fixed server paths and validated numeric booking IDs.
        # Never forward headers, tokens or credentials supplied by the browser.
        outbound = URLRequest(self._url + path, method=method,
            data=None if payload is None else json.dumps(payload).encode(), headers={
                'Authorization': 'Bearer ' + self._key, 'apikey': self._key,
                'Content-Type': 'application/json',
            })
        try:
            with build_opener(NoRedirect()).open(outbound, timeout=20) as response:
                if expect_void:
                    return None  # PostgREST void RPC may return 204 with an empty body.
                return json.load(response)
        except HTTPError as error:
            if sending:
                outcome = 'failed' if 400 <= error.code < 500 and error.code not in (408, 409) else 'unknown'
                raise SupabaseSendError(outcome, f'edge_http_{error.code}') from None
            status = error.code if error.code in (404, 409, 422) else 502
            detail = ('Invio non confermato: verificare su Resend prima di riprovare.' if sending
                      else 'Operazione comunicazioni non disponibile.')
            raise HTTPException(status_code=status, detail=detail) from None
        except (URLError, TimeoutError, OSError, ValueError):
            if sending:
                raise SupabaseSendError('unknown', 'edge_transport_uncertain') from None
            detail = ('Esito invio incerto: verificare su Resend prima di riprovare.' if sending
                      else 'Servizio comunicazioni non disponibile.')
            raise HTTPException(status_code=502, detail=detail) from None

    def require_booking(self, booking_id, *, confirmed=False):
        fields = 'id,status' if confirmed else 'id'
        rows = self.request('GET', f'/rest/v1/bookings?select={fields}&id=eq.{booking_id}&limit=1')
        if not isinstance(rows, list):
            raise HTTPException(status_code=502, detail='Prenotazione non verificabile.')
        if not rows:
            raise HTTPException(status_code=404, detail='Prenotazione non trovata.')
        if len(rows) != 1 or not isinstance(rows[0], dict) or str(rows[0].get('id')) != str(booking_id):
            raise HTTPException(status_code=502, detail='Prenotazione non verificabile.')
        if confirmed and rows[0].get('status') != 'confirmed':
            raise HTTPException(status_code=409, detail='La prenotazione non è confermata.')
        return rows[0]
