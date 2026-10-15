import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from fastapi.testclient import TestClient
from bookings.customer import token_hash, issue_management_link, customer_action
from bookings.validators import _validate
from bookings.dates import _parse
from config import TZ
import index

class CustomerManagementTests(unittest.TestCase):
    def test_random_links_store_hash_not_raw_capability(self):
        calls=[]
        class Connection:
            def execute(self,sql,args):calls.append((sql,args));return self
            def fetchone(self):return {'booking_id':42}
        first=issue_management_link(Connection(),42)
        second=issue_management_link(Connection(),42)
        self.assertNotEqual(first,second)
        token=first.split('=')[1]
        self.assertEqual(len(token),43)
        self.assertEqual(calls[1][1][0],token_hash(token))
        self.assertNotIn(token,calls[1][1])
        self.assertNotIn('42',first.split('#')[0])
        for invalid in ['42','../bookings/42','!'*43,None]:
            with self.assertRaises(ValueError):token_hash(invalid)
    def test_public_management_actions_are_server_validated_and_private(self):
        client=TestClient(index.app)
        for action,body in [('view',{}),('reconfirm',{}),('request',{'request_type':'cancellazione','requested_value':None,'operation_id':'00000000-0000-4000-8000-000000000001'})]:
            index._hits.clear()
            with patch('index.customer_action',return_value={'ok':True}) as service:
                response=client.post('/api/booking-management/'+action,json={'token':'a'*43,**body})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['cache-control'],'no-store')
            self.assertEqual(service.call_args.args[0],'a'*43)
        index._hits.clear()
        with patch('index.customer_action',return_value={'ok':True,'outcome':'pending'}):
            response=client.post('/api/booking-management/request',json={'token':'a'*43,'request_type':'data','requested_value':'2026-10-20','operation_id':'00000000-0000-4000-8000-000000000002'})
        self.assertEqual(response.status_code,202)
        index._hits.clear()
        with patch('index.customer_action',return_value={'ok':True,'outcome':'cancelled','_booking_id':42,'_communication_id':13}),patch('index.send_customer_action_email') as send:
            response=client.post('/api/booking-management/request',json={'token':'a'*43,'request_type':'cancellazione','operation_id':'00000000-0000-4000-8000-000000000003'})
        self.assertEqual(response.status_code,200)
        self.assertNotIn('_booking_id',response.json())
        send.assert_called_once_with(42,13)
        with patch('index.customer_action',side_effect=ValueError('secret')):
            index._hits.clear()
            self.assertEqual(client.post('/api/booking-management/view',json={'token':'a'*43}).status_code,404)
        with patch('index.customer_action') as service:
            index._hits.clear()
            self.assertEqual(client.post('/api/booking-management/request',json={'token':'a'*43,'booking_id':42,'request_type':'note','requested_value':'test'}).status_code,422)
            service.assert_not_called()
    def test_invalid_token_never_opens_database_and_read_never_updates_booking(self):
        with patch('bookings.customer.db') as database:
            with self.assertRaises(ValueError):customer_action('42','request','cancellazione',None)
            database.assert_not_called()
        statements=[]
        class Connection:
            def execute(self,sql,args=()):statements.append((sql,args));return self
            def fetchone(self):return {'result':{'name':'Cliente','status':'confirmed'}}
        @contextmanager
        def database(write=False):
            self.assertFalse(write);yield Connection()
        with patch('bookings.customer.db',database):result=customer_action('a'*43,'view')
        self.assertEqual(result['status'],'confirmed')
        self.assertEqual(statements[0][0],'SET TRANSACTION READ ONLY')
        self.assertFalse(any('UPDATE' in sql or 'INSERT' in sql for sql,args in statements))
    def test_midnight_validates_service_day_and_exact_booking_slots(self):
        self.assertEqual(_parse('2026-10-10','00:00').date().isoformat(),'2026-10-11')
        with patch('bookings.validators.now_local',return_value=datetime(2026,10,10,12,tzinfo=TZ)):
            self.assertIsNone(_validate('2026-10-10','00:00',2,'dopocena')[1])
            self.assertIsNotNone(_validate('2026-10-10','00:00',2,'normale')[1])
            self.assertIsNotNone(_validate('2026-10-10','18:30',2)[1])
            self.assertIsNotNone(_validate('2026-10-10','23:00',2)[1])
            self.assertIsNone(_validate('2026-10-10','22:30',2)[1])
            # Sunday midnight belongs to the Sunday service, despite Monday closure.
            self.assertIsNone(_validate('2026-10-11','00:00',2,'dopocena')[1])
            self.assertIsNotNone(_validate('2026-10-12','00:00',2,'dopocena')[1])
    def test_reminder_worker_is_dry_run_by_default_and_reuses_existing_sender(self):
        import importlib.util
        import argparse
        import io
        spec=importlib.util.spec_from_file_location('reminder_worker',Path(__file__).resolve().parents[1]/'scripts/booking_reminders.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        statements=[]
        class Connection:
            def execute(self,sql,args=()):statements.append(sql);return self
            def fetchall(self):return [{'id':42}]
        @contextmanager
        def database(write=False):
            self.assertFalse(write);yield Connection()
        with patch.object(worker,'db',database),patch.object(worker.argparse.ArgumentParser,'parse_args',return_value=argparse.Namespace(prepare=False,send=False)),patch.object(worker,'prepare_reminder') as prepare,patch.object(worker,'send_claimed_email') as send,patch('sys.stdout',io.StringIO()):
            worker.main()
        prepare.assert_not_called();send.assert_not_called()
        self.assertEqual(statements[0],'SET TRANSACTION READ ONLY')
        self.assertTrue(all('INSERT' not in sql and 'UPDATE' not in sql for sql in statements))
