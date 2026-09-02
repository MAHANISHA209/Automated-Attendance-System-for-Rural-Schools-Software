from flask import Blueprint, request, jsonify
from datetime import datetime, date
import calendar
from backend.database import get_db
from backend.middleware.auth import token_required

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@report_bp.route('/student/<student_id>', methods=['GET'])
@token_required
def get_student_report(student_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT s.*, c.class_name, c.section, p.name as parent_name, p.phone as parent_phone
    FROM students s
    JOIN classes c ON s.class_id = c.id
    LEFT JOIN parents p ON s.parent_id = p.id
    WHERE s.id = ?
    """, (student_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return jsonify({'success': False, 'message': 'Student not found.'}), 404

    query = "SELECT date, time, status, remarks FROM attendance WHERE student_id = ?"
    params = [student_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"
    cursor.execute(query, params)
    records = [dict(r) for r in cursor.fetchall()]

    total_days = len(records)
    present_days = sum(1 for r in records if r['status'] == 'Present')
    absent_days = sum(1 for r in records if r['status'] == 'Absent')
    late_days = sum(1 for r in records if r['status'] == 'Late')

    # Formula: (Present Days / Total Working Days) * 100
    percentage = round((present_days / total_days * 100), 2) if total_days > 0 else 0.0

    cursor.execute("SELECT value FROM settings WHERE key = 'low_attendance_threshold'")
    thresh_row = cursor.fetchone()
    threshold = float(thresh_row['value']) if thresh_row else 75.0

    conn.close()

    return jsonify({
        'success': True,
        'student': dict(student),
        'summary': {
            'total_working_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'percentage': percentage,
            'threshold': threshold,
            'is_low_attendance': percentage < threshold and total_days >= 5
        },
        'records': records
    })

@report_bp.route('/class/<class_id>', methods=['GET'])
@token_required
def get_class_report(class_id):
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT c.*, t.name as teacher_name FROM classes c LEFT JOIN teachers t ON c.teacher_id = t.id WHERE c.id = ?", (class_id,))
    cls = cursor.fetchone()
    if not cls:
        conn.close()
        return jsonify({'success': False, 'message': 'Class not found.'}), 404

    cursor.execute("SELECT * FROM students WHERE class_id = ? AND status = 'active' ORDER BY roll_number", (class_id,))
    students = [dict(r) for r in cursor.fetchall()]

    date_filter = ""
    params = [class_id]
    if start_date and end_date:
        date_filter = "AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif month:
        date_filter = "AND strftime('%Y-%m', date) = ?"
        params.append(month)

    cursor.execute("SELECT value FROM settings WHERE key = 'low_attendance_threshold'")
    thresh_row = cursor.fetchone()
    threshold = float(thresh_row['value']) if thresh_row else 75.0

    student_reports = []
    class_total_days = 0
    class_present_total = 0
    class_absent_total = 0
    class_late_total = 0

    for s in students:
        s_params = [s['id']]
        if start_date and end_date:
            s_q = f"SELECT status FROM attendance WHERE student_id = ? AND date BETWEEN ? AND ?"
            s_params.extend([start_date, end_date])
        elif month:
            s_q = f"SELECT status FROM attendance WHERE student_id = ? AND strftime('%Y-%m', date) = ?"
            s_params.append(month)
        else:
            s_q = f"SELECT status FROM attendance WHERE student_id = ?"

        cursor.execute(s_q, s_params)
        att_rows = cursor.fetchall()

        tot = len(att_rows)
        prs = sum(1 for r in att_rows if r['status'] == 'Present')
        ab = sum(1 for r in att_rows if r['status'] == 'Absent')
        lt = sum(1 for r in att_rows if r['status'] == 'Late')
        pct = round((prs / tot * 100), 1) if tot > 0 else 0.0

        class_total_days += tot
        class_present_total += prs
        class_absent_total += ab
        class_late_total += lt

        student_reports.append({
            'id': s['id'],
            'student_id': s['student_id'],
            'name': s['name'],
            'roll_number': s['roll_number'],
            'gender': s['gender'],
            'phone': s['phone'],
            'total_days': tot,
            'present_days': prs,
            'absent_days': ab,
            'late_days': lt,
            'percentage': pct,
            'is_low_attendance': pct < threshold and tot >= 5
        })

    class_avg_pct = round((class_present_total / class_total_days * 100), 1) if class_total_days > 0 else 0.0

    conn.close()

    return jsonify({
        'success': True,
        'class': dict(cls),
        'period': month or f"{start_date} to {end_date}",
        'summary': {
            'total_students': len(students),
            'class_avg_percentage': class_avg_pct,
            'threshold': threshold,
            'low_attendance_students_count': sum(1 for sr in student_reports if sr['is_low_attendance'])
        },
        'students': student_reports
    })

@report_bp.route('/matrix/<class_id>', methods=['GET'])
@token_required
def get_monthly_matrix(class_id):
    month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
    year, month = map(int, month_str.split('-'))
    num_days = calendar.monthrange(year, month)[1]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT c.*, t.name as teacher_name FROM classes c LEFT JOIN teachers t ON c.teacher_id = t.id WHERE c.id = ?", (class_id,))
    cls = cursor.fetchone()
    if not cls:
        conn.close()
        return jsonify({'success': False, 'message': 'Class not found.'}), 404

    cursor.execute("SELECT * FROM students WHERE class_id = ? AND status = 'active' ORDER BY roll_number", (class_id,))
    students = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
    SELECT student_id, date, status
    FROM attendance
    WHERE class_id = ? AND strftime('%Y-%m', date) = ?
    """, (class_id, month_str))
    records = cursor.fetchall()
    conn.close()

    att_map = {}
    for r in records:
        key = f"{r['student_id']}_{r['date']}"
        att_map[key] = r['status']

    days_list = [f"{year:04d}-{month:02d}-{d:02d}" for d in range(1, num_days + 1)]

    matrix = []
    for s in students:
        row = {
            'student_id': s['student_id'],
            'name': s['name'],
            'roll_number': s['roll_number'],
            'days': {},
            'present_count': 0,
            'absent_count': 0,
            'late_count': 0,
            'total_recorded': 0
        }
        for d in days_list:
            st = att_map.get(f"{s['id']}_{d}", '-')
            row['days'][d] = st
            if st == 'Present':
                row['present_count'] += 1
                row['total_recorded'] += 1
            elif st == 'Absent':
                row['absent_count'] += 1
                row['total_recorded'] += 1
            elif st == 'Late':
                row['late_count'] += 1
                row['total_recorded'] += 1

        tot = row['total_recorded']
        prs = row['present_count']
        row['percentage'] = round((prs / tot * 100), 1) if tot > 0 else 0.0
        matrix.append(row)

    return jsonify({
        'success': True,
        'class': dict(cls),
        'month': month_str,
        'days': days_list,
        'matrix': matrix
    })

@report_bp.route('/low-attendance', methods=['GET'])
@token_required
def get_low_attendance_alerts():
    class_id = request.args.get('class_id')
    threshold_param = request.args.get('threshold')

    conn = get_db()
    cursor = conn.cursor()

    if threshold_param:
        threshold = float(threshold_param)
    else:
        cursor.execute("SELECT value FROM settings WHERE key = 'low_attendance_threshold'")
        thresh_row = cursor.fetchone()
        threshold = float(thresh_row['value']) if thresh_row else 75.0

    query = """
    SELECT s.id, s.student_id, s.name, s.gender, s.phone, s.roll_number,
           c.class_name, c.section, c.id as class_id,
           p.name as parent_name, p.phone as parent_phone,
           COUNT(a.id) as total_working_days,
           SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
           SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
           SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_days
    FROM students s
    JOIN classes c ON s.class_id = c.id
    LEFT JOIN parents p ON s.parent_id = p.id
    LEFT JOIN attendance a ON s.id = a.student_id
    WHERE s.status = 'active'
    """
    params = []

    if class_id:
        query += " AND s.class_id = ?"
        params.append(class_id)

    query += """
    GROUP BY s.id
    HAVING total_working_days >= 3 AND (CAST(present_days AS FLOAT) / total_working_days * 100) < ?
    ORDER BY (CAST(present_days AS FLOAT) / total_working_days * 100) ASC, c.class_name, s.roll_number
    """
    params.append(threshold)

    cursor.execute(query, params)
    raw_list = [dict(r) for r in cursor.fetchall()]
    conn.close()

    result = []
    for r in raw_list:
        tot = r['total_working_days'] or 0
        prs = r['present_days'] or 0
        pct = round((prs / tot * 100), 1) if tot > 0 else 0.0
        r['percentage'] = pct
        r['threshold'] = threshold
        r['shortage'] = round(threshold - pct, 1)
        result.append(r)

    return jsonify({
        'success': True,
        'threshold': threshold,
        'count': len(result),
        'students': result
    })
