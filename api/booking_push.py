"""Server-side dispatch for a newly committed online booking push."""
import logging
import re

from supabase_server import SupabaseServer

logger = logging.getLogger("makai")


def _confirmed_online_booking(rows, booking_id):
    if not isinstance(rows, list) or len(rows) != 1:
        raise RuntimeError('Prenotazione non verificabile per la notifica push.')
    booking = rows[0]
    if (not isinstance(booking, dict)
            or booking.get('id') != booking_id
            or booking.get('source') != 'booking'
            or booking.get('status') != 'confirmed'
            or not isinstance(booking.get('name'), str)
            or not booking['name'].strip()
            or not isinstance(booking.get('booking_date'), str)
            or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', booking['booking_date'])
            or not isinstance(booking.get('booking_time'), str)
            or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?', booking['booking_time'])
            or type(booking.get('party_size')) is not int
            or not 1 <= booking['party_size'] <= 6):
        raise RuntimeError('Prenotazione non valida per la notifica push.')
    return {
        'id': booking_id,
        'source': 'booking',
        'status': 'confirmed',
        'name': booking['name'].strip(),
        'booking_date': booking['booking_date'],
        'booking_time': booking['booking_time'],
        'party_size': booking['party_size'],
    }


def _validated_edge_result(result):
    if not isinstance(result, dict) or result.get('queued') is not True:
        raise RuntimeError('La Edge Function non ha confermato la notifica push.')

    counts = {}
    for field in ('sent', 'failed', 'stale'):
        value = result.get(field)
        if type(value) is not int or value < 0:
            raise RuntimeError('Risposta non valida dalla Edge Function push.')
        counts[field] = value

    if counts['failed']:
        logger.warning(
            'Consegna push parziale: sent=%d stale=%d failed=%d.',
            counts['sent'], counts['stale'], counts['failed'],
        )
    return {'queued': True, **counts}


def send_new_online_booking_push(booking_id):
    """Send one server-authenticated Edge Function request for a committed booking."""
    if type(booking_id) is not int or booking_id < 1:
        raise ValueError('ID prenotazione non valido per la notifica push.')

    server = SupabaseServer()
    rows = server.request(
        'GET',
        '/rest/v1/bookings?select=id,source,status,name,booking_date,booking_time,party_size'
        f'&id=eq.{booking_id}&limit=1',
    )
    booking = _confirmed_online_booking(rows, booking_id)
    result = server.request(
        'POST',
        '/functions/v1/web-push-admin',
        {'action': 'new-online-booking', 'booking': booking},
    )
    return _validated_edge_result(result)
