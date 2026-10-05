"""API comunicazioni: JWT solo per auth; operazioni Supabase solo service_role."""
import re
from typing import Literal
import logging

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request
from pydantic import BaseModel, ConfigDict

from admin_auth import require_admin, require_browser_action
from supabase_server import SupabaseServer, SupabaseSendError

router = APIRouter(prefix='/api/admin/bookings', tags=['admin'])
logger = logging.getLogger('makai')
COMMUNICATION_FIELDS = ('id', 'booking_id', 'channel', 'kind', 'status', 'snapshot', 'recipient',
                        'created_at', 'attempted_at', 'error_code', 'provider_id', 'attempts')


class PrepareBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    channel: Literal['email', 'whatsapp'] = 'email'


class SendBody(BaseModel):
    model_config = ConfigDict(extra='forbid')


def authorize(request: Request):
    require_browser_action(request)
    if not request.headers.get('Authorization', '').startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Sessione Supabase richiesta.')
    require_admin(request, allowed_roles=('admin',))


def public_communication(row, booking_id):
    if not isinstance(row, dict) or str(row.get('booking_id')) != str(booking_id):
        raise HTTPException(status_code=502, detail='Comunicazione non confermata.')
    return {key: row[key] for key in COMMUNICATION_FIELDS if key in row}


@router.get('/{booking_id}/communications', dependencies=[Depends(authorize)])
def list_communications(booking_id: int = Path(gt=0)):
    server = SupabaseServer()
    server.require_booking(booking_id)
    fields = ','.join(COMMUNICATION_FIELDS)
    rows = server.request('GET', f'/rest/v1/booking_communications?select={fields}&booking_id=eq.{booking_id}&order=id.desc')
    if not isinstance(rows, list):
        raise HTTPException(status_code=502, detail='Comunicazioni non disponibili.')
    return {'communications': [public_communication(row, booking_id) for row in rows]}


@router.post('/{booking_id}/communications/prepare', dependencies=[Depends(authorize)])
def prepare_communication(booking_id: int = Path(gt=0), body: PrepareBody = Body(default=PrepareBody())):
    server = SupabaseServer()
    server.require_booking(booking_id)
    result = server.request('POST', '/rest/v1/rpc/admin_prepare_booking_communication',
                            {'p_booking_id': booking_id, 'p_channel': body.channel})
    row = public_communication(result, booking_id)
    if row.get('channel') != body.channel:
        raise HTTPException(status_code=502, detail='Preparazione della comunicazione non confermata.')
    return {'communication': row}


def email_outcome(result, booking_id, communication_id):
    # A malformed success or lost response may conceal an accepted email.
    if (not isinstance(result, dict) or result.get('bookingId') != booking_id
            or result.get('communicationId') != communication_id or result.get('type') != 'booking_confirmation'
            or result.get('status') not in ('accepted', 'failed', 'unknown')):
        return 'unknown', None, 'edge_invalid_response'
    if result['status'] == 'accepted':
        provider_id = result.get('emailId')
        if not isinstance(provider_id, str) or not provider_id or len(provider_id) > 256:
            return 'unknown', None, 'edge_invalid_response'
        return 'accepted', provider_id, None
    code = result.get('errorCode', '')
    # Log only protocol codes, never free text returned by an upstream service.
    if not isinstance(code, str) or not re.fullmatch(
            r'(?:provider_http|provider_uncertain)_[0-9]{3}|network_uncertain|provider_invalid_response|'
            r'stale_booking|invalid_email|invalid_booking|email_not_configured|communication_unavailable', code):
        code = 'edge_failed' if result['status'] == 'failed' else 'edge_uncertain'
    return result['status'], None, code


@router.post('/{booking_id}/send-confirmation-email', dependencies=[Depends(authorize)])
def send_confirmation_email(booking_id: int = Path(gt=0), body: SendBody = Body(default=SendBody())):
    server = SupabaseServer()
    server.require_booking(booking_id, confirmed=True)
    prepared = public_communication(server.request('POST', '/rest/v1/rpc/admin_prepare_booking_communication',
        {'p_booking_id': booking_id, 'p_channel': 'email'}), booking_id)
    communication_id = prepared.get('id')
    if (type(communication_id) is not int or communication_id < 1 or prepared.get('channel') != 'email'
            or prepared.get('kind') not in ('confirmation', 'updated')):
        raise HTTPException(status_code=502, detail='Comunicazione email non confermata.')
    if prepared.get('status') == 'skipped':
        raise HTTPException(status_code=422, detail='Email della prenotazione assente o non valida.')
    claimed = server.request('POST', '/rest/v1/rpc/claim_booking_email', {'p_id': communication_id})
    if claimed is None:
        # The database is the authority; never call Edge or finish after a lost claim.
        raise HTTPException(status_code=409, detail='Comunicazione già gestita, non più valida o invio in corso.')
    return send_claimed_email(server, claimed, booking_id, communication_id)


def send_claimed_email(server, claimed, booking_id, communication_id):
    claimed = public_communication(claimed, booking_id)
    if (claimed.get('id') != communication_id or claimed.get('status') != 'sending'
            or claimed.get('channel') != 'email' or claimed.get('kind') not in ('confirmation', 'updated')):
        raise HTTPException(status_code=502, detail='Tentativo email non confermato.')
    try:
        result = server.request('POST', '/functions/v1/send-booking-email',
            {'bookingId': booking_id, 'type': 'booking_confirmation', 'communicationId': communication_id}, sending=True)
        outcome, provider_id, error_code = email_outcome(result, booking_id, communication_id)
    except SupabaseSendError as error:
        outcome, provider_id, error_code = error.outcome, None, error.error_code
    try:
        server.request('POST', '/rest/v1/rpc/finish_booking_email', {'p_id': communication_id,
            'p_status': outcome, 'p_provider_id': provider_id, 'p_error_code': error_code}, expect_void=True)
    except HTTPException:
        # A lost finish response leaves accepted/unknown/sending protected by SQL.
        # No retry of Edge, claim or finish: operator must inspect the persisted state.
        raise HTTPException(status_code=502,
            detail='Esito email non registrato: verificare comunicazioni e Resend prima di riprovare.') from None
    return JSONResponse(status_code=200 if outcome == 'accepted' else 502, content={
        'bookingId': booking_id, 'type': 'booking_confirmation', 'communicationId': communication_id,
        'status': outcome, 'emailId': provider_id, 'errorCode': error_code,
    })


def send_new_online_booking_email(booking_id):
    """One automatic attempt for a newly committed site booking, never a retry/backfill.

    The RPC verifies source, initial queued event and attempts=0 under the booking
    lock. It shares the manual claim so a simultaneous Agenda send cannot duplicate it.
    Email errors never turn a committed booking into a public booking failure.
    """
    try:
        server = SupabaseServer()
        claimed = server.request('POST', '/rest/v1/rpc/claim_new_online_booking_email',
                                 {'p_booking_id': booking_id})
        if claimed is None:
            return
        communication_id = claimed.get('id') if isinstance(claimed, dict) else None
        if (type(communication_id) is not int or communication_id < 1
                or claimed.get('kind') != 'confirmation'):
            raise HTTPException(status_code=502, detail='Tentativo email non confermato.')
        response = send_claimed_email(server, claimed, booking_id, communication_id)
        if response.status_code != 200:
            logger.warning('Conferma email automatica non accettata; consultare il log Agenda.')
    except Exception:
        # Never log exception bodies, contacts, credentials or provider details.
        logger.warning('Conferma email automatica non confermata; consultare il log Agenda.')
