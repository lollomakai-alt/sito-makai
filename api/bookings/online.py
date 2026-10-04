"""Online requests: atomic consent, idempotent retries, staff-only table assignment."""
import hashlib
import json
import re
from uuid import UUID
from config import MAX_ACTIVE_PER_PHONE
from database import db
from .validators import normalize_booking_name, normalize_phone, normalize_email, _validate
from .service import _upcoming_for_phone

PRIVACY_VERSION = "2026-10-04-online-v1"
MARKETING_VERSION = "2026-10-04-online-v1"
MARKETING_TEXT = "Voglio ricevere sconti, offerte e novità di Makai tramite WhatsApp."


def create_online_booking(name, phone, date, time, party_size, request_id,
                          privacy=False, marketing=False, email="", notes=""):
    name = normalize_booking_name(name)
    phone = normalize_phone(phone)
    normalized_email = normalize_email(email) if email else ""
    if not name or not phone or normalized_email is None:
        return {"ok": False, "error": "Inserisci nome e cognome e contatti validi."}
    if privacy is not True or type(marketing) is not bool:
        return {"ok": False, "error": "Devi leggere l’informativa privacy. Marketing facoltativo."}
    if type(party_size) is not int or not 1 <= party_size <= 6 or len(notes) > 300:
        return {"ok": False, "error": "Coperti o note non validi."}
    try:
        request_id = str(UUID(str(request_id)))
    except (ValueError, TypeError):
        return {"ok": False, "error": "Richiesta non valida. Ricarica la pagina."}
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date) or not re.fullmatch(r"[0-9]{2}:(00|30)", time):
        return {"ok": False, "error": "Data o ora non valide."}
    notes = notes.strip()
    fingerprint = hashlib.sha256(json.dumps([name, phone, normalized_email, date, time,
        party_size, notes, privacy, marketing], ensure_ascii=False).encode()).hexdigest()
    with db(write=True) as c:
        c.execute("SET LOCAL statement_timeout = '8000ms'")
        previous = c.execute(
            "SELECT r.fingerprint, b.id, b.status FROM private.online_booking_receipts r "
            "JOIN public.bookings b ON b.id=r.booking_id WHERE r.request_id=%s", (request_id,),
        ).fetchone()
        if previous:
            if previous['fingerprint'] != fingerprint:
                return {"ok": False, "error": "Richiesta già utilizzata con altri dati. Ricarica la pagina."}
            return {"ok": True, "booking_id": previous['id'], "status": previous['status'], "replayed": True}
        dt, error = _validate(date, time, party_size)
        if error:
            return {"ok": False, "error": error}
        if len(_upcoming_for_phone(c, phone)) >= MAX_ACTIVE_PER_PHONE:
            return {"ok": False, "error": "Questo telefono ha già due prenotazioni attive. Per altre chiamaci."}
        status = c.execute("SELECT private.online_day_status(%s,%s,NULL) AS status", (date,party_size)).fetchone()['status']
        if status != 'available':
            return {"ok": False, "error": "Disponibilità cambiata o non verificabile. Aggiorna il calendario o chiamaci."}
        saved = c.execute(
            "INSERT INTO public.bookings(name,email,phone,booking_date,booking_time,party_size,notes,"
            "tables,status,source,reminder_status,privacy_accepted_at,privacy_version) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,'','confirmed','booking','skipped',now(),%s) RETURNING id,tables,status",
            (name,normalized_email,phone,date,time,party_size,notes,PRIVACY_VERSION),
        ).fetchone()
        if saved['tables'] or saved['status'] != 'confirmed':
            raise RuntimeError('Online booking SQL not installed correctly')
        c.execute("INSERT INTO private.online_booking_receipts(request_id,booking_id,fingerprint) VALUES (%s,%s,%s)",
                  (request_id,saved['id'],fingerprint))
        if marketing:
            existing = c.execute("SELECT id FROM public.marketing_contacts WHERE phone=%s FOR UPDATE", (phone,)).fetchone()
            values = (name,phone,saved['id'],MARKETING_TEXT,MARKETING_VERSION,PRIVACY_VERSION)
            if existing:
                c.execute("UPDATE public.marketing_contacts SET nome=%s,phone=%s,booking_id=%s,canale='whatsapp',"
                          "consenso_testo=%s,consenso_versione=%s,privacy_versione=%s,risposta='Sì, checkbox sul sito',"
                          "consenso_data=now(),scadenza_consenso=now()+interval '24 months',revocato_il=NULL,"
                          "rinnovi=rinnovi+1,registrato_da='sito',updated_at=now() WHERE id=%s", values+(existing['id'],))
            else:
                c.execute("INSERT INTO public.marketing_contacts(nome,phone,booking_id,canale,consenso_testo,"
                          "consenso_versione,privacy_versione,risposta,consenso_data,scadenza_consenso,"
                          "rinnovi,registrato_da,fonte,updated_at) VALUES (%s,%s,%s,'whatsapp',%s,%s,%s,"
                          "'Sì, checkbox sul sito',now(),now()+interval '24 months',1,'sito','booking',now())", values)
        return {"ok": True, "booking_id": saved['id'], "status": 'confirmed', "replayed": False}
