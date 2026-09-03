from flask import Blueprint, request, jsonify
from datetime import datetime, date
from backend.database import get_db
from backend.middleware.auth import token_required, roles_accepted

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

@attendance_bp.route('/sheet', methods=['GET'])
@token_required
def get_class_sheet():
    class_id = request.args.get('class_id')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    subject_id = request.args.get('subject_id')

    if not class_id:
        return jsonify({'success': False, 'message': 'Class ID is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT s.id as student_id, s.name, s.gender, s.roll_number, s.student_id as student_code,
           a.id as attendance_id, a.status, a.time, a.remarks
    FROM students s
    LEFT JOIN attendance a ON a.student_id = s.id AND a.class_id = ? AND a.date = ?
    WHERE s.class_id = ? AND s.status = 'active'
    ORDER BY s.roll_number, s.name
    """, (class_id, date_str, class_id))
    students = [dict(r) for r in cursor.fetchall()]

    # Format students: if attendance not marked, default to None (frontend can show 'Present' toggle)
    already_marked = any(s['attendance_id'] is not None for s in students)

    cursor.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
    cls = cursor.fetchone()

    cursor.execute("SELECT * FROM subjects WHERE class_id = ?", (class_id,))
    subjects = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        'success': True,
        'class': dict(cls) if cls else None,
        'date': date_str,
        'already_marked': already_marked,
        'students': students,
        'subjects': subjects
    })

@attendance_bp.route('/check-duplicate', methods=['GET'])
@token_required
def check_duplicate():
    class_id = request.args.get('class_id')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    subject_id = request.args.get('subject_id')

    if not class_id:
        return jsonify({'success': False, 'message': 'Class ID is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(*) as count, MIN(time) as first_time, MAX(updated_at) as last_updated
    FROM attendance
    WHERE class_id = ? AND date = ?
    """, (class_id, date_str))
    res = dict(cursor.fetchone())
    conn.close()

    is_duplicate = res['count'] > 0
    return jsonify({
        'success': True,
        'is_duplicate': is_duplicate,
        'records_count': res['count'],
        'first_time': res['first_time'],
        'last_updated': res['last_updated'],
        'message': 'Attendance already recorded for this class on the selected date.' if is_duplicate else 'No duplicate records found.'
    })

@attendance_bp.route('/batch', methods=['POST'])
@token_required
@roles_accepted('admin', 'principal', 'teacher')
def mark_batch_attendance():
    data = request.get_json() or {}
    class_id = data.get('class_id')
    date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    time_str = data.get('time', datetime.now().strftime('%H:%M:%S'))
    subject_id = data.get('subject_id')
    records = data.get('records', [])
    override = data.get('override', False)

    if not class_id or not records:
        return jsonify({'success': False, 'message': 'Class ID and records are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if duplicate exists without override
    cursor.execute("SELECT COUNT(*) as cnt FROM attendance WHERE class_id = ? AND date = ?", (class_id, date_str))
    existing_cnt = cursor.fetchone()['cnt']
    if existing_cnt > 0 and not override:
        conn.close()
        return jsonify({
            'success': False,
            'is_duplicate': True,
            'message': f'Attendance for this class on {date_str} already exists ({existing_cnt} records). Confirm overwrite to update.'
        }), 409

    teacher_id = None
    if request.current_user['role'] == 'teacher':
        cursor.execute("SELECT id FROM teachers WHERE user_id = ?", (request.current_user['id'],))
        t_row = cursor.fetchone()
        if t_row: teacher_id = t_row['id']
    else:
        teacher_id = request.current_user['id']

    saved_count = 0
    for r in records:
        sid = r.get('student_id')
        status = r.get('status', 'Present')
        remarks = r.get('remarks', '')
        if sid:
            cursor.execute("""
            INSERT OR REPLACE INTO attendance (student_id, class_id, teacher_id, subject_id, date, time, status, remarks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (sid, class_id, teacher_id, subject_id, date_str, time_str, status, remarks))
            saved_count += 1

    # Add notification for principal/admin
    cursor.execute("SELECT class_name, section FROM classes WHERE id = ?", (class_id,))
    c_info = cursor.fetchone()
    c_name = f"{c_info['class_name']}-{c_info['section']}" if c_info else "Class"

    cursor.execute("""
    INSERT INTO notifications (user_id, title, message, type, is_read, created_at)
    SELECT id, 'Attendance Submitted', ?, 'info', 0, CURRENT_TIMESTAMP
    FROM users WHERE role IN ('admin', 'principal')
    """, (f"Attendance for {c_name} on {date_str} marked by {request.current_user['name']} ({saved_count} students).",))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': f'Attendance successfully saved for {saved_count} students in {c_name}.',
        'saved_count': saved_count
    })

@attendance_bp.route('/history', methods=['GET'])
@token_required
def get_attendance_history():
    class_id = request.args.get('class_id')
    student_id = request.args.get('student_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    offset = (page - 1) * limit

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT a.*, s.name as student_name, s.roll_number, s.student_id as student_code,
           c.class_name, c.section, u.name as marked_by_name
    FROM attendance a
    JOIN students s ON a.student_id = s.id
    JOIN classes c ON a.class_id = c.id
    LEFT JOIN users u ON a.teacher_id = u.id
    WHERE 1=1
    """
    params = []

    if class_id:
        query += " AND a.class_id = ?"
        params.append(class_id)

    if student_id:
        query += " AND a.student_id = ?"
        params.append(student_id)

    if start_date:
        query += " AND a.date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND a.date <= ?"
        params.append(end_date)

    if status:
        query += " AND a.status = ?"
        params.append(status)

    count_query = f"SELECT COUNT(*) as total FROM ({query})"
    cursor.execute(count_query, params)
    total_records = cursor.fetchone()['total']

    query += " ORDER BY a.date DESC, a.time DESC, s.roll_number LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({
        'success': True,
        'records': records,
        'total': total_records,
        'page': page,
        'limit': limit
    })

@attendance_bp.route('/calendar', methods=['GET'])
@token_required
def get_calendar_attendance():
    student_id = request.args.get('student_id')
    class_id = request.args.get('class_id')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT date, status, COUNT(*) as count FROM attendance WHERE strftime('%Y-%m', date) = ?"
    params = [month]

    if student_id:
        query += " AND student_id = ? GROUP BY date, status"
        params.append(student_id)
    elif class_id:
        query += " AND class_id = ? GROUP BY date, status"
        params.append(class_id)
    else:
        query += " GROUP BY date, status"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Group by date
    calendar_map = {}
    for r in rows:
        d = r['date']
        if d not in calendar_map:
            calendar_map[d] = {'Present': 0, 'Absent': 0, 'Late': 0, 'total': 0}
        calendar_map[d][r['status']] = r['count']
        calendar_map[d]['total'] += r['count']

    return jsonify({
        'success': True,
        'month': month,
        'calendar': calendar_map
    })
