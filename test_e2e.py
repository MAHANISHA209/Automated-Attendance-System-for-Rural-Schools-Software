import unittest
import json
from app import create_app
from backend.database import get_db

class TestAutomatedAttendanceSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_health_and_index(self):
        # Health check
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'online')

        # Static index check
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('Automated Attendance System', html)
        self.assertIn('Smart Attendance Management for Rural Schools', html)
        self.assertIn('education_banner.jpg', html)

    def test_02_authentication_roles(self):
        roles = [
            ('admin', 'Admin@123', 'admin'),
            ('principal', 'Principal@123', 'principal'),
            ('teacher', 'Teacher@123', 'teacher'),
            ('student', 'Student@123', 'student'),
            ('parent', 'Parent@123', 'parent')
        ]
        for username, password, expected_role in roles:
            res = self.client.post('/api/auth/login', json={'username': username, 'password': password})
            self.assertEqual(res.status_code, 200, f"Login failed for {username}")
            data = res.get_json()
            self.assertTrue(data['success'])
            self.assertIn('token', data)
            self.assertEqual(data['user']['role'], expected_role)

    def test_03_dashboard_stats(self):
        # Test Admin Dashboard
        login_res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})
        admin_token = login_res.get_json()['token']
        res = self.client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {admin_token}'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('total_students', data['stats'])

        # Test Teacher Dashboard
        login_res = self.client.post('/api/auth/login', json={'username': 'teacher', 'password': 'Teacher@123'})
        teacher_token = login_res.get_json()['token']
        res = self.client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {teacher_token}'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['role'], 'teacher')

        # Test Student Dashboard
        login_res = self.client.post('/api/auth/login', json={'username': 'student', 'password': 'Student@123'})
        student_token = login_res.get_json()['token']
        res = self.client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {student_token}'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['role'], 'student')
        self.assertIn('attendance_percentage', data['stats'])

        # Test Parent Dashboard
        login_res = self.client.post('/api/auth/login', json={'username': 'parent', 'password': 'Parent@123'})
        parent_token = login_res.get_json()['token']
        res = self.client.get('/api/dashboard/stats', headers={'Authorization': f'Bearer {parent_token}'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['role'], 'parent')
        self.assertTrue(len(data['children']) > 0)

    def test_04_mark_attendance_flow(self):
        login_res = self.client.post('/api/auth/login', json={'username': 'teacher', 'password': 'Teacher@123'})
        token = login_res.get_json()['token']

        # Get sheet for Class 8 (id 4)
        sheet_res = self.client.get('/api/attendance/sheet?class_id=4&date=2026-08-24', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(sheet_res.status_code, 200)
        sheet_data = sheet_res.get_json()
        self.assertTrue(sheet_data['success'])
        students = sheet_data['students']
        self.assertTrue(len(students) > 0)

        # Batch mark attendance
        records = [
            {'student_id': students[0]['student_id'], 'status': 'Present', 'remarks': 'On time'},
            {'student_id': students[1]['student_id'], 'status': 'Absent', 'remarks': 'Sick fever'},
            {'student_id': students[2]['student_id'], 'status': 'Late', 'remarks': 'Late by 15 mins'}
        ]
        batch_res = self.client.post('/api/attendance/batch', 
                                    headers={'Authorization': f'Bearer {token}'},
                                    json={'class_id': 4, 'date': '2026-08-24', 'records': records, 'override': True})
        self.assertEqual(batch_res.status_code, 200)
        batch_data = batch_res.get_json()
        self.assertTrue(batch_data['success'])
        self.assertEqual(batch_data['saved_count'], 3)

    def test_05_reports_and_export(self):
        login_res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})
        token = login_res.get_json()['token']

        # Class report
        res = self.client.get('/api/reports/class/4?month=2026-08', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('students', data)

        # Matrix report
        res_m = self.client.get('/api/reports/matrix/4?month=2026-08', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res_m.status_code, 200)
        data_m = res_m.get_json()
        self.assertTrue(data_m['success'])
        self.assertIn('matrix', data_m)

        # Student report
        res = self.client.get('/api/reports/student/1', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('summary', data)

        # CSV Exports
        res = self.client.get('/api/export/attendance/csv', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')

        res = self.client.get('/api/export/low-attendance/csv', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')

    def test_06_crud_classes_students_teachers(self):
        login_res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})
        token = login_res.get_json()['token']

        # List classes
        res = self.client.get('/api/classes', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()['classes']) >= 6)

        # List students
        res = self.client.get('/api/students', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()['students']) > 0)

        # List teachers
        res = self.client.get('/api/teachers', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()['teachers']) >= 5)

if __name__ == '__main__':
    unittest.main()
