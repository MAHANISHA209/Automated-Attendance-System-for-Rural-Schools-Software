from flask import Blueprint, request, jsonify, Response
import csv
import io
from datetime import datetime
from backend.database import get_db
from backend.middleware.auth import token_required

export_bp = Blueprint('export', __name__, url_prefix='/api/export')

@export_bp.route('/attendance/csv', methods=['GET'])
@token_required
def export_attendance_csv():
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT a.date, a.time, s.student_id, s.name as student_name, s.roll_number,
           c.class_name, c.section, a.status, a.remarks, u.name as marked_by
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
    if start_date:
        query += " AND a.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND a.date <= ?"
        params.append(end_date)

    query += " ORDER BY a.date DESC, c.class_name, s.roll_number"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Time', 'Student ID', 'Student Name', 'Roll No', 'Class', 'Section', 'Status', 'Remarks', 'Marked By'])
    for r in rows:
        cw.writerow([r['date'], r['time'], r['student_id'], r['student_name'], r['roll_number'], r['class_name'], r['section'], r['status'], r['remarks'] or '', r['marked_by'] or ''])

    filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    res = Response(si.getvalue(), mimetype='text/csv')
    res.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return res

@export_bp.route('/low-attendance/csv', methods=['GET'])
@token_required
def export_low_attendance_csv():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'low_attendance_threshold'")
    thresh_row = cursor.fetchone()
    threshold = float(thresh_row['value']) if thresh_row else 75.0

    query = """
    SELECT s.student_id, s.name as student_name, s.roll_number, s.phone,
           c.class_name, c.section, p.name as parent_name, p.phone as parent_phone,
           COUNT(a.id) as total_days,
           SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
           SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_days
    FROM students s
    JOIN classes c ON s.class_id = c.id
    LEFT JOIN parents p ON s.parent_id = p.id
    LEFT JOIN attendance a ON s.id = a.student_id
    WHERE s.status = 'active'
    GROUP BY s.id
    HAVING total_days >= 3 AND (CAST(present_days AS FLOAT) / total_days * 100) < ?
    ORDER BY (CAST(present_days AS FLOAT) / total_days * 100) ASC
    """
    cursor.execute(query, (threshold,))
    rows = cursor.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student ID', 'Student Name', 'Roll No', 'Class', 'Section', 'Parent Name', 'Parent Phone', 'Total Working Days', 'Present Days', 'Absent Days', 'Attendance %', 'Threshold %'])
    for r in rows:
        tot = r['total_days'] or 0
        prs = r['present_days'] or 0
        pct = round((prs / tot * 100), 1) if tot > 0 else 0.0
        cw.writerow([r['student_id'], r['student_name'], r['roll_number'], r['class_name'], r['section'], r['parent_name'] or '', r['parent_phone'] or '', tot, prs, r['absent_days'] or 0, f"{pct}%", f"{threshold}%"])

    filename = f"low_attendance_alert_{datetime.now().strftime('%Y%m%d')}.csv"
    res = Response(si.getvalue(), mimetype='text/csv')
    res.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return res
