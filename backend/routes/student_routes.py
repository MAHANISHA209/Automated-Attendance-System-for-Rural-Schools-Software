from flask import Blueprint, request, jsonify, Response
from backend.database import get_db
from backend.middleware.auth import token_required, roles_accepted
import csv
import io
from datetime import datetime

student_bp = Blueprint('students', __name__, url_prefix='/api/students')

@student_bp.route('', methods=['GET'])
@token_required
def get_students():
    search = request.args.get('search', '').strip()
    class_id = request.args.get('class_id', '').strip()
    section = request.args.get('section', '').strip()
    status = request.args.get('status', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    
    query = """
    SELECT st.*, c.class_name, c.section, p.name as parent_name, p.phone as parent_phone, p.email as parent_email
    FROM students st
    JOIN classes c ON st.class_id = c.id
    LEFT JOIN parents p ON st.parent_id = p.id
    WHERE 1=1
    """
    params = []

    if search:
        query += " AND (st.name LIKE ? OR st.student_id LIKE ? OR st.roll_number LIKE ?)"
        term = f'%{search}%'
        params.extend([term, term, term])

    if class_id:
        query += " AND st.class_id = ?"
        params.append(class_id)

    if section:
        query += " AND st.section = ?"
        params.append(section)

    if status:
        query += " AND st.status = ?"
        params.append(status)

    query += " ORDER BY c.class_name, st.roll_number, st.name"
    cursor.execute(query, params)
    students = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({'success': True, 'students': students, 'total': len(students)})

@student_bp.route('/<id>', methods=['GET'])
@token_required
def get_student_detail(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT st.*, c.class_name, c.section, p.name as parent_name, p.phone as parent_phone, p.email as parent_email, p.address as parent_address
    FROM students st
    JOIN classes c ON st.class_id = c.id
    LEFT JOIN parents p ON st.parent_id = p.id
    WHERE st.id = ?
    """, (id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'success': False, 'message': 'Student not found.'}), 404

    cursor.execute("""
    SELECT COUNT(*) as total_days,
           SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
           SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
           SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days
    FROM attendance WHERE student_id = ?
    """, (id,))
    stats = dict(cursor.fetchone())
    tot = stats['total_days'] or 0
    prs = stats['present_days'] or 0
    stats['attendance_percentage'] = round((prs / tot * 100), 1) if tot > 0 else 0

    conn.close()
    return jsonify({'success': True, 'student': dict(student), 'stats': stats})

@student_bp.route('', methods=['POST'])
@token_required
@roles_accepted('admin', 'principal')
def add_student():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    gender = data.get('gender', 'Male').strip()
    dob = data.get('date_of_birth', '').strip()
    class_id = data.get('class_id')
    section = data.get('section', 'A').strip()
    roll_number = data.get('roll_number', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    admission_date = data.get('admission_date', '').strip() or datetime.now().strftime('%Y-%m-%d')
    parent_name = data.get('parent_name', '').strip()
    parent_phone = data.get('parent_phone', '').strip()
    status = data.get('status', 'active')

    if not name or not dob or not class_id or not roll_number:
        return jsonify({'success': False, 'message': 'Name, Date of Birth, Class, and Roll Number are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM students WHERE class_id = ? AND section = ? AND roll_number = ?', (class_id, section, roll_number))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Roll number already exists in this class section.'}), 400

    cursor.execute('SELECT MAX(id) as max_id FROM students')
    max_id = (cursor.fetchone()['max_id'] or 0) + 1
    student_id = f"STD-{class_id}{max_id:02d}"
    
    parent_id = None
    if parent_name or parent_phone:
        cursor.execute('SELECT id FROM parents WHERE phone = ?', (parent_phone,))
        prow = cursor.fetchone()
        if prow:
            parent_id = prow['id']
        else:
            pid = f"PAR-{max_id:03d}"
            cursor.execute('INSERT INTO parents (parent_id, name, phone, address, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', (pid, parent_name or 'Parent', parent_phone or '+91 00000 00000', address))
            parent_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO students (student_id, name, gender, date_of_birth, class_id, section, roll_number, parent_id, phone, address, admission_date, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (student_id, name, gender, dob, class_id, section, roll_number, parent_id, phone, address, admission_date, status))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Student added successfully.'})

@student_bp.route('/<id>', methods=['PUT'])
@token_required
@roles_accepted('admin', 'principal')
def update_student(id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    gender = data.get('gender', 'Male').strip()
    dob = data.get('date_of_birth', '').strip()
    class_id = data.get('class_id')
    section = data.get('section', 'A').strip()
    roll_number = data.get('roll_number', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    status = data.get('status', 'active')

    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE students SET name = ?, gender = ?, date_of_birth = ?, class_id = ?, section = ?, roll_number = ?, phone = ?, address = ?, status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (name, gender, dob, class_id, section, roll_number, phone, address, status, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Student updated successfully.'})

@student_bp.route('/<id>', methods=['DELETE'])
@token_required
@roles_accepted('admin', 'principal')
def delete_student(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Student deleted successfully.'})

@student_bp.route('/export', methods=['GET'])
@token_required
def export_students():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT st.student_id, st.name, st.gender, st.date_of_birth, c.class_name, st.section, st.roll_number, p.name as parent_name, st.phone, st.address, st.admission_date, st.status
    FROM students st
    JOIN classes c ON st.class_id = c.id
    LEFT JOIN parents p ON st.parent_id = p.id
    ORDER BY c.class_name, st.roll_number
    """)
    rows = cursor.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student ID', 'Full Name', 'Gender', 'DOB', 'Class', 'Section', 'Roll No', 'Parent Name', 'Phone', 'Address', 'Admission Date', 'Status'])
    for r in rows:
        cw.writerow([r['student_id'], r['name'], r['gender'], r['date_of_birth'], r['class_name'], r['section'], r['roll_number'], r['parent_name'] or '', r['phone'] or '', r['address'] or '', r['admission_date'] or '', r['status']])

    response = Response(si.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=students_list.csv"
    return response
