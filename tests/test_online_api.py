import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from fastapi.testclient import TestClient
import index

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(index.app)
        index._hits.clear()
        self.body=dict(name='Mario Rossi',phone='+393331234567',date='2026-10-06',time='20:00',party_size=2,privacy=True,marketing=False,request_id='11111111-1111-4111-8111-111111111111')
    def test_public_create_and_idempotent_response_no_admin_gateway(self):
        with patch('index.create_online_booking',return_value={'ok':True,'booking_id':42,'status':'confirmed','replayed':False}) as create:
            response=self.client.post('/api/bookings',json=self.body)
            self.assertEqual(response.status_code,201)
            self.assertEqual(response.headers['cache-control'],'no-store')
            self.assertEqual(create.call_args.kwargs['marketing'],False)
        with patch('index.create_online_booking',return_value={'ok':True,'booking_id':42,'status':'confirmed','replayed':True}):
            self.assertEqual(self.client.post('/api/bookings',json=self.body).status_code,200)
    def test_strict_fields_reject_injected_state_and_fake_consent_before_service(self):
        with patch('index.create_online_booking') as create:
            for extra in [{'tables':'12'},{'source':'agenda'},{'status':'arrived'},{'user_id':'someone'},{'party_size':True},{'party_size':7},{'privacy':'true'},{'marketing':1}]:
                self.assertEqual(self.client.post('/api/bookings',json=self.body|extra).status_code,422)
            create.assert_not_called()
    def test_failures_do_not_leak_database_details(self):
        with patch('index.create_online_booking',return_value={'ok':False,'error':'Disponibilità cambiata'}):
            self.assertEqual(self.client.post('/api/bookings',json=self.body).status_code,409)
        with patch('index.create_online_booking',side_effect=RuntimeError('private credentials')):
            response=self.client.post('/api/bookings',json=self.body)
            self.assertEqual(response.status_code,503)
            self.assertNotIn('credentials',response.text)
    def test_settings_provide_real_slots_and_privacy_version(self):
        data=self.client.get('/api/booking-settings').json()
        self.assertEqual(data['times'][0],'18:00');self.assertEqual(data['times'][-1],'23:00')
        self.assertEqual(data['privacy_version'],'2026-10-04-online-v1')
