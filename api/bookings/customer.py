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
        "INSERT INTO private.booking_customer_tokens(token_hash,booking_id,expires_at) "
        "SELECT %s,id,private.booking_scheduled_at(booking_date,booking_time)+interval '30 days' FROM public.bookings WHERE id=%s",
        (token_hash(token), booking_id))
    origin=os.environ.get('PUBLIC_SITE_URL','https://www.makaipigneto.it').rstrip('/')
    parsed=urlsplit(origin)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Origine sito pubblico non valida.')
    management_url=origin+'/prenotazioni/gestisci#token='+token
    connection.execute("UPDATE public.booking_communications SET snapshot=jsonb_set(snapshot,'{management_url}',to_jsonb(%s::text)) WHERE booking_id=%s AND kind IN ('confirmation','updated') AND status='queued'",(management_url,booking_id))
    # Fragment is never sent in the request URL, access logs or Referer.
    return "/prenotazioni/gestisci#token=" + token

def customer_action(token, action, request_type=None, requested_value=None):
    digest = token_hash(token)
    with db(write=action != "view") as connection:
        if action == "view":
            connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL statement_timeout='8000ms'")
        if action == "view":
            row = connection.execute("SELECT private.customer_booking(%s) AS result", (digest,)).fetchone()
        elif action == "request":
            row = connection.execute("SELECT private.customer_booking_request(%s,%s,%s::jsonb) AS result",
                                     (digest, request_type, json.dumps(requested_value))).fetchone()
        elif action == "reconfirm":
            row = connection.execute("SELECT private.reconfirm_customer_booking(%s) AS result", (digest,)).fetchone()
        else:
            raise ValueError("Operazione non valida.")
        if not row or row.get("result") is None:
            raise ValueError("Collegamento non valido o scaduto.")
        return row["result"]
