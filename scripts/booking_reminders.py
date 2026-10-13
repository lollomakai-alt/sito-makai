"""Dry-run by default. Use --prepare to queue, --send to dispatch through existing Edge."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from database import db
from bookings.reminders import prepare_reminder
from booking_communications import send_claimed_email
from supabase_server import SupabaseServer

def main():
    parser=argparse.ArgumentParser(description='Reminder Makai del giorno precedente')
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--send',action='store_true')
    args=parser.parse_args()
    with db() as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        rows=connection.execute("SELECT id FROM public.bookings WHERE status='confirmed' AND booking_date=to_char((now() at time zone 'Europe/Rome')::date+1,'YYYY-MM-DD') AND coalesce(email,'')<>'' ORDER BY id").fetchall()
    print('Prenotazioni da verificare:',len(rows))
    if not(args.prepare or args.send):return
    for row in rows:prepare_reminder(row['id'])
    if args.send:
        # Only a queued reminder for tomorrow; unknown/failed are never retried automatically.
        with db() as connection:
            connection.execute('SET TRANSACTION READ ONLY')
            pending=connection.execute("SELECT c.id,c.booking_id FROM public.booking_communications c JOIN public.bookings b ON b.id=c.booking_id WHERE c.kind='reminder' AND c.status='queued' AND b.status='confirmed' AND b.booking_date=to_char((now() at time zone 'Europe/Rome')::date+1,'YYYY-MM-DD') ORDER BY c.id").fetchall()
        server=SupabaseServer()
        for c in pending:
            claimed=server.request('POST','/rest/v1/rpc/claim_booking_email',{'p_id':c['id']})
            if claimed is not None:send_claimed_email(server,claimed,c['booking_id'],c['id'])
if __name__=='__main__':main()
