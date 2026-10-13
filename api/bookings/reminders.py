"""Explicit reminder preparation. No scheduling or sending happens on import."""
from database import db
from .customer import issue_management_link

def prepare_reminder(booking_id):
    with db(write=True) as connection:
        row=connection.execute("SELECT id FROM public.bookings WHERE id=%s AND status='confirmed' AND booking_date=to_char((now() at time zone 'Europe/Rome')::date+1,'YYYY-MM-DD') AND coalesce(email,'')<>'' FOR UPDATE",(booking_id,)).fetchone()
        if not row:return None
        existing=connection.execute("SELECT id FROM public.booking_communications WHERE event_key=%s",('reminder:'+str(booking_id)+':'+connection.execute("SELECT booking_date FROM public.bookings WHERE id=%s",(booking_id,)).fetchone()['booking_date'],)).fetchone()
        if existing:return None
        relative=issue_management_link(connection,booking_id)
        import os
        url=os.environ.get('PUBLIC_SITE_URL','https://www.makaipigneto.it').rstrip('/')+relative
        return connection.execute("SELECT private.prepare_booking_reminder(%s,%s) AS result",(booking_id,url)).fetchone()['result']
