import sys
import unittest
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from bookings.online import create_online_booking
from config import TZ

class OnlineTests(unittest.TestCase):
    def run_booking(self,previous=None,status='available',marketing=False,privacy=True,existing=None,assigned='12'):
        self.calls=[]
        class Connection:
            def execute(_,sql,args=None): self.calls.append((sql,args)); return _
            def fetchone(_):
                sql=self.calls[-1][0]
                if 'private.site_maintenance' in sql:return {'active':False}
                if 'online_booking_receipts r' in sql:return previous
                if 'online_slot_status' in sql:return {'status':status}
                if 'INSERT INTO public.bookings' in sql:return {'id':42,'tables':assigned,'status':'confirmed'}
                if 'marketing_contacts WHERE' in sql:return existing
                raise AssertionError(sql)
        @contextmanager
        def database(write=False):
            self.assertTrue(write);yield Connection()
        with patch('bookings.online.db',database),patch('bookings.online._upcoming_for_phone',return_value=[]),patch('bookings.online.issue_management_link',return_value='/prenotazioni/gestisci#token='+'a'*43),patch('bookings.validators.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)):
            return create_online_booking('Mario Rossi','3331234567','2026-10-06','20:00',2,'11111111-1111-4111-8111-111111111111',privacy=privacy,marketing=marketing)
    def test_confirmed_auto_assigned_and_no_marketing_when_unchecked(self):
        result=self.run_booking()
        self.assertTrue(result['ok']);self.assertEqual(result['booking_id'],42)
        insert=next(sql for sql,args in self.calls if 'INSERT INTO public.bookings' in sql)
        self.assertIn("'','confirmed','booking','skipped'",insert)
        self.assertIn('privacy_accepted_at,privacy_version',insert)
        self.assertFalse(any('marketing_contacts' in sql for sql,args in self.calls))
        self.assertTrue(any('INSERT INTO private.online_booking_receipts' in sql for sql,args in self.calls))
    def test_optional_marketing_create_and_renew(self):
        self.run_booking(marketing=True)
        self.assertTrue(any('INSERT INTO public.marketing_contacts' in sql for sql,args in self.calls))
        self.run_booking(marketing=True,existing={'id':8})
        self.assertTrue(any('rinnovi=rinnovi+1' in sql for sql,args in self.calls))
    def test_replay_no_double_booking_or_consent_even_after_admin_cancel(self):
        self.run_booking(marketing=True)
        fingerprint=next(args[2] for sql,args in self.calls if 'INSERT INTO private.online_booking_receipts' in sql)
        result=self.run_booking(marketing=True,previous={'id':42,'status':'cancelled','fingerprint':fingerprint})
        self.assertTrue(result['replayed']);self.assertEqual(result['status'],'cancelled')
        self.assertFalse(any('INSERT' in sql or 'UPDATE' in sql for sql,args in self.calls))
        result=self.run_booking(previous={'id':42,'status':'confirmed','fingerprint':'different'})
        self.assertFalse(result['ok'])
    def test_closure_capacity_or_unknown_never_write(self):
        for status in ['closed','full','unverified']:
            self.assertFalse(self.run_booking(status=status)['ok'])
            self.assertFalse(any('INSERT' in sql for sql,args in self.calls))
    def test_privacy_required_before_db(self):
        with patch('bookings.online.db') as database:
            result=self.run_booking(privacy=False)
            self.assertFalse(result['ok']);database.assert_not_called()
    def test_missing_dinner_assignment_aborts_transaction(self):
        with self.assertRaises(RuntimeError):self.run_booking(assigned='')
    def test_missing_slot_rpc_aborts_without_inserting_booking(self):
        statements=[]
        class Connection:
            def execute(self,sql,args=None):
                statements.append(sql)
                if 'private.online_slot_status' in sql:
                    raise RuntimeError('function private.online_slot_status does not exist')
                return self
            def fetchone(self):
                return {'active':False} if 'private.site_maintenance' in statements[-1] else None
        @contextmanager
        def database(write=False):
            self.assertTrue(write)
            yield Connection()
        with patch('bookings.online.db',database),patch('bookings.online._upcoming_for_phone',return_value=[]),patch('bookings.validators.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)):
            with self.assertRaisesRegex(RuntimeError,'online_slot_status'):
                create_online_booking('Mario Rossi','3331234567','2026-10-06','20:00',2,
                    '11111111-1111-4111-8111-111111111111',privacy=True)
        self.assertFalse(any('INSERT INTO public.bookings' in sql for sql in statements))

    def test_dopocena_creates_pending_request_without_booking_or_marketing(self):
        statements=[]
        class Connection:
            def execute(_,sql,args=None): statements.append((sql,args)); return _
            def fetchone(_):
                sql=statements[-1][0]
                if 'private.site_maintenance' in sql:return {'active':False}
                if 'FROM private.online_dopocena_requests' in sql:return None
                if 'private.online_slot_status' in sql:return {'status':'manual_review'}
                if 'INSERT INTO private.online_dopocena_requests' in sql:return {'status':'pending'}
                if 'marketing_contacts WHERE' in sql:return None
                raise AssertionError(sql)
        @contextmanager
        def database(write=False): self.assertTrue(write); yield Connection()
        request_id='11111111-1111-4111-8111-111111111111'
        with patch('bookings.online.db',database),patch('bookings.online._upcoming_for_phone',return_value=[]),patch('bookings.validators.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)):
            result=create_online_booking('Mario Rossi','3331234567','2026-10-06','23:00',2,request_id,privacy=True,booking_type='dopocena')
        self.assertEqual(result,{'ok':True,'request_id':request_id,'status':'pending','replayed':False,'booking_type':'dopocena'})
        insert=next((sql,args) for sql,args in statements if 'INSERT INTO private.online_dopocena_requests' in sql)
        self.assertIn('ON CONFLICT (request_id) DO NOTHING',insert[0])
        self.assertFalse(any('INSERT INTO public.bookings' in sql or 'online_booking_receipts' in sql for sql,args in statements))
        self.assertFalse(any('marketing_contacts' in sql for sql,args in statements))

    def test_dopocena_retry_replays_pending_request_and_rejects_changed_payload(self):
        import hashlib, json
        fingerprint=hashlib.sha256(json.dumps(
            ['Mario Rossi','+393331234567','','2026-10-06','23:00',2,'',True,False,'dopocena'],ensure_ascii=False).encode()).hexdigest()
        previous={'fingerprint':fingerprint,'status':'pending'}
        statements=[]
        class Connection:
            def execute(_,sql,args=None): statements.append((sql,args)); return _
            def fetchone(_):
                if 'private.site_maintenance' in statements[-1][0]:return {'active':False}
                if 'FROM private.online_dopocena_requests' in statements[-1][0]:return previous
                raise AssertionError(statements[-1][0])
        @contextmanager
        def database(write=False): self.assertTrue(write); yield Connection()
        with patch('bookings.online.db',database):
            replay=create_online_booking('Mario Rossi','3331234567','2026-10-06','23:00',2,'11111111-1111-4111-8111-111111111111',privacy=True,booking_type='dopocena')
            changed=create_online_booking('Mario Rossi','3331234567','2026-10-06','23:30',2,'11111111-1111-4111-8111-111111111111',privacy=True,booking_type='dopocena')
        self.assertTrue(replay['replayed']); self.assertEqual(replay['status'],'pending')
        self.assertFalse(changed['ok'])
        self.assertEqual(sum('private.online_slot_status' in sql for sql,args in statements),0)

    def test_optional_dopocena_marketing_records_evidence_and_24_month_expiry(self):
        statements=[]
        class Connection:
            def execute(_,sql,args=None): statements.append((sql,args)); return _
            def fetchone(_):
                sql=statements[-1][0]
                if 'private.site_maintenance' in sql:return {'active':False}
                if 'FROM private.online_dopocena_requests' in sql:return None
                if 'private.online_slot_status' in sql:return {'status':'manual_review'}
                if 'INSERT INTO private.online_dopocena_requests' in sql:return {'status':'pending'}
                if 'marketing_contacts WHERE' in sql:return None
                raise AssertionError(sql)
        @contextmanager
        def database(write=False): self.assertTrue(write); yield Connection()
        with patch('bookings.online.db',database),patch('bookings.online._upcoming_for_phone',return_value=[]),patch('bookings.validators.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)):
            result=create_online_booking('Mario Rossi','3331234567','2026-10-06','23:00',2,
                '11111111-1111-4111-8111-111111111111',privacy=True,marketing=True,booking_type='dopocena')
        self.assertEqual(result['status'],'pending')
        insert=next(sql for sql,args in statements if 'INSERT INTO public.marketing_contacts' in sql)
        self.assertIn("'Sì, checkbox sul sito'",insert)
        self.assertIn("now()+interval '24 months'",insert)
        args=next(args for sql,args in statements if 'INSERT INTO public.marketing_contacts' in sql)
        self.assertIsNone(args[2])  # no booking exists until the staff accepts the request

if __name__=='__main__':unittest.main()
