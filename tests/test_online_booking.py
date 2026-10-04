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
    def run_booking(self,previous=None,status='available',marketing=False,privacy=True,existing=None,assigned=''):
        self.calls=[]
        class Connection:
            def execute(_,sql,args=None): self.calls.append((sql,args)); return _
            def fetchone(_):
                sql=self.calls[-1][0]
                if 'online_booking_receipts r' in sql:return previous
                if 'online_day_status' in sql:return {'status':status}
                if 'INSERT INTO public.bookings' in sql:return {'id':42,'tables':assigned,'status':'confirmed'}
                if 'marketing_contacts WHERE' in sql:return existing
                raise AssertionError(sql)
        @contextmanager
        def database(write=False):
            self.assertTrue(write);yield Connection()
        with patch('bookings.online.db',database),patch('bookings.online._upcoming_for_phone',return_value=[]),patch('bookings.validators.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)):
            return create_online_booking('Mario Rossi','3331234567','2026-10-06','20:00',2,'11111111-1111-4111-8111-111111111111',privacy=privacy,marketing=marketing)
    def test_confirmed_unassigned_and_no_marketing_when_unchecked(self):
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
    def test_old_auto_assignment_aborts_transaction(self):
        with self.assertRaises(RuntimeError):self.run_booking(assigned='12')

if __name__=='__main__':unittest.main()
