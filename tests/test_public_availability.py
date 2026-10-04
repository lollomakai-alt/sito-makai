import sys
import unittest
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from config import TZ
from bookings.public_availability import month_availability

class AvailabilityTests(unittest.TestCase):
    def calendar(self,rows=(),people=2):
        statements=[]
        class Connection:
            def execute(self,sql,args=None): statements.append((sql,args)); return self
            def fetchall(self): return rows
        @contextmanager
        def database(): yield Connection()
        with patch('bookings.public_availability.db',database),patch('bookings.public_availability.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)):
            result=month_availability('2026-10',people)
        self.assertEqual(statements[0][0],'SET TRANSACTION READ ONLY')
        self.assertIn('private.online_day_status',statements[2][0])
        self.assertNotIn('name',statements[2][0])
        self.assertEqual(statements[2][1],(people,'2026-10-03','2026-10-31'))
        return {d['date']:d['status'] for d in result['days']}
    def test_shared_statuses_closed_unknown_full_and_unassigned(self):
        days=self.calendar([{'booking_date':'2026-10-06','status':'available'}, {'booking_date':'2026-10-07','status':'full'}, {'booking_date':'2026-10-08','status':'unverified'}, {'booking_date':'2026-10-09','status':'closed'}])
        self.assertEqual(days['2026-10-06'],'available')
        self.assertEqual(days['2026-10-07'],'full')
        self.assertEqual(days['2026-10-08'],'unverified')
        self.assertEqual(days['2026-10-09'],'closed')
        self.assertEqual(days['2026-10-05'],'closed')
        self.assertEqual(days['2026-10-02'],'past')
        self.assertEqual(days['2026-10-10'],'unverified')
    def test_invalid_request_no_database_access(self):
        with patch('bookings.public_availability.db') as database:
            for month,size in [('2026-13',2),('2026-10',True),('2026-10',7),('2026-10',0),('0000-01',2)]:
                with self.assertRaises(ValueError): month_availability(month,size)
            database.assert_not_called()
    def test_offline_never_reports_available(self):
        with patch('bookings.public_availability.now_local',return_value=datetime(2026,10,3,12,tzinfo=TZ)),patch('bookings.public_availability.db',side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError): month_availability('2026-10',2)
