"""Customer possession links: random capability, hashed storage, server validation."""
import json
import hashlib
import re
import secrets
import os
from urllib.parse import urlsplit
from database import db

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")

def token_hash(token):
    if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
        raise ValueError("Collegamento non valido o scaduto.")
    return hashlib.sha256(token.encode("ascii")).hexdigest()

def issue_management_link(connection, booking_id):
    token = secrets.token_urlsafe(32)
    connection.execute(
        "UPDATE private.booking_customer_tokens SET revoked_at=now() "
        "WHERE booking_id=%s AND revoked_at IS NULL", (booking_id,))
    inserted = connection.execute(
        "INSERT INTO private.booking_customer_tokens(token_hash,booking_id,expires_at) "
        "SELECT %s,id,private.booking_scheduled_at(booking_date,booking_time)+interval '30 days' "
        "FROM public.bookings WHERE id=%s RETURNING booking_id",
        (token_hash(token), booking_id)).fetchone()
    if not inserted:
        raise ValueError('Prenotazione non disponibile.')
    origin=os.environ.get('PUBLIC_SITE_URL','https://www.makaipigneto.it').rstrip('/')
    parsed=urlsplit(origin)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Origine sito pubblico non valida.')
    management_url=origin+'/prenotazioni/gestisci#token='+token
    connection.execute("UPDATE public.booking_communications SET snapshot=jsonb_set(snapshot,'{management_url}',to_jsonb(%s::text)) WHERE booking_id=%s AND kind IN ('confirmation','updated') AND status='queued'",(management_url,booking_id))
    # Fragment is never sent in the request URL, access logs or Referer.
    return "/prenotazioni/gestisci#token=" + token

def customer_action(token, action, request_type=None, requested_value=None, operation_id=None):
    digest = token_hash(token)
    with db(write=action != "view") as connection:
        if action == "view":
            connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL statement_timeout='8000ms'")
        if action == "view":
            row = connection.execute("SELECT private.customer_booking(%s) AS result", (digest,)).fetchone()
        elif action == "request":
            if not operation_id:
                raise ValueError('Operazione non valida.')
            row = connection.execute("SELECT private.customer_booking_request(%s,%s,%s::jsonb,%s::uuid) AS result",
                                     (digest, request_type, json.dumps(requested_value), str(operation_id))).fetchone()
        elif action == "reconfirm":
            row = connection.execute("SELECT private.reconfirm_customer_booking(%s) AS result", (digest,)).fetchone()
        else:
            raise ValueError("Operazione non valida.")
        if not row or row.get("result") is None:
            raise ValueError("Collegamento non valido o scaduto.")
        result = row["result"]
        if action == 'request' and result.get('outcome') in ('applied', 'cancelled'):
            origin = os.environ.get('PUBLIC_SITE_URL','https://www.makaipigneto.it').rstrip('/')
            parsed = urlsplit(origin)
            if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
                raise ValueError('Origine sito pubblico non valida.')
            booking = connection.execute(
                "SELECT booking_id FROM private.booking_customer_tokens WHERE token_hash=%s", (digest,)
            ).fetchone()
            communication = connection.execute(
                "UPDATE public.booking_communications SET snapshot=jsonb_set(snapshot,'{management_url}',to_jsonb(%s::text)) "
                "WHERE id=(SELECT id FROM public.booking_communications WHERE booking_id=%s AND channel='email' "
                "AND kind IN ('updated','cancelled') AND status='queued' ORDER BY id DESC LIMIT 1) "
                "RETURNING id", (origin+'/prenotazioni/gestisci#token='+token, booking['booking_id'])
            ).fetchone()
            if communication:
                result['_communication_id'] = communication['id']
                result['_booking_id'] = booking['booking_id']
        return result
