import sqlite3
import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from backend.config import Config

def get_db():
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL CHECK (role IN ('admin', 'principal', 'teacher', 'student', 'parent')), phone TEXT, status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')), avatar TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTs parents (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, email TEXT, phone TEXT NOT NULL, address TEXT, user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL, gender TEXT DEFAULT 'Male', qualification TEXT, subject TEXT, address TEXT, status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')), user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT NOT NULL, section TEXT NOT NULL, teacher_id INTEGER, academic_year TEXT NOT NULL DEFAULT '2026-2027', room_number TEXT, status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL, UNIQUE(class_name, section, academic_year));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_name TEXT NOT NULL, class_id INTEGER, teacher_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE, FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, gender TEXT NOT NULL CHECK(gender IN ('Male', 'Female', 'Other')), date_of_birth DATE NOT NULL, class_id INTEGER NOT NULL, section TEXT NOT NULL, roll_number TEXT NOT NULL, parent_id INTEGER, phone TEXT, address TEXT, admission_date DATE, photo TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')), user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE RESTRICT, FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE SET NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL, UNIQUE(class_id, section, roll_number));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, class_id INTEGER NOT NULL, teacher_id INTEGER, subject_id INTEGER, date DATE NOT NULL, time TIME NOT NULL, status TEXT NOT NULL CHECK (status IN ('Present', 'Absent', 'Late')), remarks TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE, FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL, FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL, UNIQUE(student_id, class_id, date, subject_id));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, message TEXT NOT NULL, type TEXT NOT NULL DEFAULT 'info' CHECK (type IN ('info', 'alert', 'warning', 'success')), is_read INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTs settings (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL, value TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
    conn.commit()
    conn.close()
    print('Database schema initialized!')


def seed_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM users')
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        print('Data already exists, skipping seed.')
        return
    print('Seeding demo database...')
    settings_data = [
        ('school_name', 'Green Valley Rural Model School'),
        ('school_tagline', 'Empowering Rural Education through Smart Digital Governance'),
        ('school_logo', '/static/images/school_logo.png'),
        ('school_address', 'Village Rampur, District Education Zone, Pin 243504'),
        ('contact_number', '+91 98765 43210'),
        ('email', 'contact@greenvalleyschool.edu.in'),
        ('academic_year', '2026-2027'),
        ('low_attendance_threshold', '75.0'),
        ('sms_notifications', 'true'),
        ('offline_sync_interval', '5'),
        ('system_theme', 'education-emerald')
    ]
    cursor.executemany('INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)', settings_data)
    users_data = [
        ('System Administrator', 'admin@greenvalleyschool.edu.in', 'admin', generate_password_hash('Admin@123'), 'admin', '+91 98765 00001', 'active'),
        ('Dr. Ramesh Sharma (Principal)', 'principal@greenvalleyschool.edu.in', 'principal', generate_password_hash('Principal@123'), 'principal', '+91 98765 00002', 'active'),
        ('Sunita Devi (Class Teacher 8A)', 'teacher@greenvalleyschool.edu.in', 'teacher', generate_password_hash('Teacher@123'), 'teacher', '+91 98765 00003', 'active'),
        ('Manoj Kumar (Science Teacher)', 'manoj@greenvalleyschool.edu.in', 'teacher_manoj', generate_password_hash('Teacher@123'), 'teacher', '+91 98765 00004', 'active'),
        ('Anjali Verma (Maths Teacher', 'anjali@greenvalleyschool.edu.in', 'teacher_anjali', generate_password_hash('Teacher@123'), 'teacher', '+91 98765 00005', 'active'),
        ('Aarav Patel (Student)', 'aarav@greenvalleyschool.edu.in', 'student', generate_password_hash('Student@123'), 'student', '+91 98765 00006', 'active'),
        ('Pooja Patel (Parent)', 'parent@greenvalleyschool.edu.in', 'parent', generate_password_hash('Parent@123'), 'parent', '+91 98765 00007', 'active')
    ]
    cursor.executemany('INSERT INTO users (name, email, username, password, role, phone, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', users_data)
    cursor.execute('SELECT id, username FROM users')
    u_dict = {row['username']: row['id'] for row in cursor.fetchall()}
    teachers_data = [
        ('TCH-001', 'Sunita Devi', 'teacher@greenvalleyschool.edu.in', '+91 98765 00003', 'Female', 'M.Sc, B.Ed (Mathematics)', 'Mathematics', 'Ward 4, Rampur Rural Zone', 'active', u_dict['teacher']),
        ('TCH-002', 'Manoj Kumar', 'manoj@greenvalleyschool.edu.in', '+91 98765 00004', 'Male', 'M.Sc (Physics), B.Ed', 'Science', 'Main Road, Rampur East', 'active', u_dict['teacher_manoj']),
        ('TCH_003', 'Anjali Verma', 'anjali@greenvalleyschool.edu.in', '+91 98765 00005', 'Female', 'M.A (English), B.Ed', 'English', 'Near High School Ground, Rampur', 'active', u_dict['teacher_anjali']),
        ('TCH-004', 'Rajesh Gupta', 'rajesh@greenvalleyschool.edu.in', '+91 98765 00008', 'Male', 'M.A (History), B.Ed', 'Social Science', 'North Rampur Colony', 'active', None),
        ('TCH-005', 'Kavita Singh', 'kavita@greenvalleyschool.edu.in', '+91 98765 00009', 'Female', 'B.Tech, B.Ed', 'Computer Basics', 'Rampur Central Block', 'active', None)
    ]
    cursor.executemany('INSERT INTO teachers (teacher_id, name, email, phone, gender, qualification, subject, address, status, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', teachers_data)
    classes_data = [
        ('Class 5', 'A', 1, '2026-2027', 'Room 101', 'active'),
        ('Class 6', 'A', 2, '2026-2027', 'Room 102', 'active'),
        ('Class 7', 'A', 3, '2026-2027', 'Room 103', 'active'),
        ('Class 8', 'A', 1, '2026-2027', 'Room 201', 'active'),
        ('Class 9', 'A', 4, '2026-2027', 'Room 202', 'active'),
        ('Class 10', 'A', 5, '2026-2027', 'Room 203', 'active')
    ]
    cursor.executemany('INSERT INTO classes (class_name, section, teacher_id, academic_year, room_number, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', classes_data)
    subjects_data = [
        ('Mathematics', 4, 1), ('Science', 4, 2), ('English', 4, 3), ('Social Science', 4, 4), ('Regional Language', 4, 1),
        ('Mathematics', 1, 1), ('General Science', 1, 2), ('English', 1, 3),
        ('Mathematics', 2, 1), ('Science', 2, 2),
        ('Mathematics', 3, 1), ('Science', 3, 2),
        ('Mathematics', 5, 1), ('Science', 5, 2),
        ('Mathematics', 6, 1), ('Science', 6, 2)
    ]
    cursor.executemany('INSERT INTO subjects (subject_name, class_id, teacher_id, created_at, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', subjects_data)

    parents_data = [
        ('PAR-001', 'Pooja Patel', 'parent@greenvalleyschool.edu.in', '+91 98765 00007', 'House No 12, Rampur Village', u_dict['parent']),
        ('PAR-002', 'Vikram Singh', 'vikram.singh@gmail.com', '+91 98765 11002', 'Farm House 4, Rampur West', None),
        ('PAR-003', 'Meena Devi', 'meena.devi@gmail.com', '+91 98765 11003', 'Near Water Tank, Rampur South', None),
        ('PAR-004', 'Dinesh Rawat', 'dinesh.rawat@gmail.com', '+91 98765 11004', 'Village Market Road, Rampur', None),
        ('PAR-005', 'Sunita Yadav', 'sunita.yadav@gmail.com', '+91 98765 11005', 'Sector 2, Rampur Extension', None),
        ('PAR-006', 'Harish Chandra', 'harish.chandra@gmail.com', '+91 98765 11006', 'Plot 8, Village Border', None),
        ('PAR-007', 'Geeta Kumari', 'geeta.kumari@gmail.com', '+91 98765 11007', 'House 22, Old Post Office Lane', None),
        ('PAR-008', 'Sanjay Kumar', 'sanjay.kumar@gmail.com', '+91 98765 11008', 'Near Panchayat Bhavan, Rampur', None)
    ]
    cursor.executemany('INSERT INTO parents (parent_id, name, email, phone, address, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', parents_data)
    students_data = [
        ('STD-801', 'Aarav Patel', 'Male', '2012-05-14', 4, 'A', '01', 1, '+91 98765 00007', 'House No 12, Rampur Village', '2022-06-15', u_dict['student']),
        ('STD-802', 'Diya Singh', 'Female', '2012-08-20', 4, 'A', '02', 2, '+91 98765 11002', 'Farm House 4, Rampur West', '2022-06-15', None),
        ('STD-803', 'Rohan Rawat', 'Male', '2012-03-10', 4, 'A', '03', 4, '+91 98765 11004', 'Village Market Road, Rampur', '2022-06-15', None),
        ('STD-804', 'Sneha Yadav', 'Female', '2012-11-25', 4, 'A', '04', 5, '+91 98765 11005', 'Sector 2, Rampur Extension', '2022-06-15', None),
        ('STD-805', 'Aditya Chandra', 'Male', '2012-01-18', 4, 'A', '05', 6, '+91 98765 11006', 'Plot 8, Village Border', '2022-06-15', None),
        ('STD-806', 'Ananya Kumari', 'Female', '2012-07-09', 4, 'A', '06', 7, '+91 98765 11007', 'House 22, Old Post Office Lane', '2022-06-15', None),
        ('STD-807', 'Kabir Kumar', 'Male', '2012-09-30', 4, 'A', '07', 8, '+91 98765 11008', 'Near Panchayat Bhavan, Rampur', '2022-06-15', None),
        ('STD-808', 'Priya Sharma', 'Female', '2012-04-12', 4, 'A', '08', 3, '+91 98765 11003', 'Near Water Tank, Rampur South', '2022-06-15', None),
        ('STD-809', 'Manish Gupta', 'Male', '2012-06-22', 4, 'A', '09', 1, '+91 98765 00007', 'House No 12, Rampur Village', '2022-06-15', None),
        ('STD-810', 'Kiran Verma', 'Female', '2012-12-05', 4, 'A', '10', 2, '+91 98765 11002', 'Farm House 4, Rampur West', '2022-06-15', None),
        ('STD-501', 'Vivaan Joshi', 'Male', '2015-02-11', 1, 'A', '01', 3, '+91 98765 11003', 'Rampur East Village', '2025-06-10', None),
        ('STD-502', 'Isha Roy', 'Female', '2015-09-14', 1, 'A', '02', 4, '+91 98765 11004', 'Rampur Central Block', '2025-06-10', None),
        ('STD-503', 'Dev Mehra', 'Male', '2015-07-22', 1, 'A', '03', 5, '+91 98765 11005', 'Station Road, Rampur', '2025-06-10', None),
        ('STD-601', 'Arjun Nair', 'Male', '2014-04-05', 2, 'A', '01', 6, '+91 98765 11006', 'South Rampur Block', '2024-06-12', None),
        ('STD-602', 'Bhavna Sen', 'Female', '2014-10-18', 2, 'A', '02', 7, '+91 98765 11007', 'Rampur High Ground', '2024-06-12', None),
        ('STD-603', 'Chetan Patil', 'Male', '2014-12-01', 2, 'A', '03', 8, '+91 98765 11008', 'Near Temple, Rampur', '2024-06-12', None),
        ('STD-701', 'Gaurav Das', 'Male', '2013-03-29', 3, 'A', '01', 1, '+91 98765 00007', 'Main Village Square', '2023-06-14', None),
        ('STD-702', 'Hina Khan', 'Female', '2013-06-17', 3, 'A', '02', 2, '+91 98765 11002', 'Near Mosque Lane, Rampur', '2023-06-14', None),
        ('STD-901', 'Mayank Tiwari', 'Male', '2011-01-25', 5, 'A', '01', 3, '+91 98765 11003', 'North Extension Rampur', '2021-06-15', None),
        ('STD-902', 'Neha Bhatt', 'Female', '2011-09-19', 5, 'A', '02', 4, '+91 98765 11004', 'Farm Road Rampur', '2021-06-15', None),
        ('STD-101', 'Tarun Saini', 'Male', '2010-05-08', 6, 'A', '01', 5, '+91 98765 11005', 'Outer Rampur Ring', '2020-06-15', None),
        ('STD-102', 'Varsha Pandey', 'Female', '2010-11-30', 6, 'A', '02', 6, '+91 98765 11006', 'Old Canal Bank, Rampur', '2020-06-15', None)
    ]
    cursor.executemany('INSERT INTO students (student_id, name, gender, date_of_birth, class_id, section, roll_number, parent_id, phone, address, admission_date, user_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \'active\', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', students_data)
    today = datetime.now().date()
    attendance_records = []
    cursor.execute('SELECT id, class_id, student_id FROM students')
    student_rows = cursor.fetchall()
    days_back = 45
    date_list = []
    for i in range(days_back, 0, -1):
        d = today - timedelta(days=i)
        if d.weekday() != 6:
            date_list.append(d)
    random.seed(42)
    for d in date_list:
        date_str = d.strftime('%Y-%m-%d')
        for s in student_rows:
            sid = s['id']
            cid = s['class_id']
            if sid == 1:
                status = random.choices(['Present', 'Late', 'Absent'], weights=[92, 5, 3])[0]
            elif sid == 3:
                status = random.choices(['Present', 'Late', 'Absent'], weights=[60, 10, 30])[0]
            elif sid == 7:
                status = random.choices(['Present', 'Late', 'Absent'], weights=[65, 5, 30])[0]
            elif sid == 2:
                status = random.choices(['Present', 'Late', 'Absent'], weights=[96, 3, 1])[0]
            else:
                status = random.choices(['Present', 'Late', 'Absent'], weights=[84, 8, 8])[0]
            time_str = '08:30:00' if status == 'Present' else ('08:52:00' if status == 'Late' else '08:30:00')
            remarks = 'Regular' if status == 'Present' else ('Bus delay' if status == 'Late' else 'Sick leave / Uninformed')
            attendance_records.append((sid, cid, 1, 1, date_str, time_str, status, remarks))
    today_str = today.strftime('%Y-%m-%d')
    for s in student_rows:
        if s['class_id'] == 4:
            sid = s['id']
            cid = s['class_id']
            if sid == 3:
                status = 'Absent'
                remarks = 'Parent notified: Fever'
            elif sid == 5:
                status = 'Late'
                remarks = 'Arrived 20 mins late'
            else:
                status = 'Present'
                remarks = 'Marked on time'
            attendance_records.append((sid, cid, 1, 1, today_str, '08:30:00', status, remarks))
    cursor.executemany('INSERT OR REPLACE INTO attendance (student_id, class_id, teacher_id, subject_id, date, time, status, remarks, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', attendance_records)
    notifications_data = [
        (u_dict['student'], 'Attendance Recorded', 'Your attendance for today has been marked as Present.', 'success', 0),
        (u_dict['parent'], 'Daily Attendance Update', 'Aarav Patel was marked Present in Class 8-A today at 08:30 AM.', 'info', 0),
        (u_dict['parent'], 'Monthly Attendance Report', 'Aarav Patel achieved 93.5% attendance for last month.', 'success', 1),
        (u_dict['teacher'], 'Attendance Submission Notice', 'Class 8-A attendance has been successfully recorded for today.', 'success', 0),
        (u_dict['principal'], 'Low Attendance Alert', '2 students in Class 8-A currently have attendance below the 75% threshold.', 'warning', 0),
        (u_dict['admin'], 'System Backup & Sync', 'Automated local database integrity check passed successfully.', 'info', 1)
    ]
    cursor.executemany('INSERT INTO notifications (user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)', notifications_data)
    conn.commit()
    conn.close()
    print('Demo data seeded successfully!')

if __name__ == '__main__':
    init_db()
    seed_data()
