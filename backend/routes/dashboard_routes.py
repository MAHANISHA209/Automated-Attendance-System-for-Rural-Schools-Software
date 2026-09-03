from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.database import get_db, Config
from backend.middleware.auth import token_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    user = request.current_user
    role = user['role']
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now().strftime('%Y-%m-%d')

    if role in ('admin', 'principal'):
        cursor.execute("SELECT COUNT(*) as total_students FROM students WHERE status = 'active'")
        total_students = cursor.fetchone()['total_students']

        cursor.execute("SELECT COUNT(*) as total_teachers FROM teachers WHERE status = 'active'")
        total_teachers = cursor.fetchone()['total_teachers']

        cursor.execute("SELECT COUNT(*) as total_classes FROM classes WHERE status = 'active'")
        total_classes = cursor.fetchone()['total_classes']

        cursor.execute("SELECT status, COUNT(*) as cnt FROM attendance WHERE date = ? GROUP BY status", (today_str,))
        status_rows = cursor.fetchall()
        today_present = 0
        today_absent = 0
        today_late = 0
        for r in status_rows:
            if r['status'] == 'Present': today_present = r['cnt']
            elif r['status'] == 'Absent': today_absent = r['cnt']
            elif r['status'] == 'Late': today_late = r['cnt']

        total_schools = 1

        # 6-Month Monthly stats
        monthly_stats = []
        now = datetime.now()
        for i in range(5, -1, -1):
            m_year = now.year
            m_month = now.month - i
            while m_month <= 0:
                m_month += 12
                m_year -= 1
            
            m_prefix = f"{m_year:04d}-{m_month:02d}"
            m_name = datetime(m_year, m_month, 1).strftime('%b %Y')

            cursor.execute("""
            SELECT status, COUNT(*) as cnt FROM attendance 
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY status
            """, (m_prefix,))
            rows = cursor.fetchall()
            p_cnt = 0
            a_cnt = 0
            l_cnt = 0
            for r in rows:
                if r['status'] == 'Present': p_cnt = r['cnt']
                elif r['status'] == 'Absent': a_cnt = r['cnt']
                elif r['status'] == 'Late': l_cnt = r['cnt']

            tot = p_cnt + a_cnt + l_cnt
            pct = round((p_cnt / tot * 100), 1) if tot > 0 else 0
            monthly_stats.append({
                'month': m_name,
                'present': p_cnt,
                'absent': a_cnt,
                'late': l_cnt,
                'total': tot,
                'percentage': pct
            })

        cursor.execute("""
        SELECT a.id, a.date, a.time, a.status, a.remarks, 
               s.name as student_name, s.roll_number,
               c.class_name, c.section,
               u.name as marked_by
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN classes c ON a.class_id = c.id
        LEFT JOIN users u ON a.teacher_id = u.id
        ORDER BY a.date DESC, a.time DESC, a.id DESC
        LIMIT 10
        """)
        recent_attendance = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
        SELECT c.id as class_id, c.class_name, c.section,
               COUNT(s.id) as total_students,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_today,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_today,
               SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_today
        FROM classes c
        LEFT JOIN students s ON s.class_id = c.id AND s.status = 'active'
        LEFT JOIN attendance a ON a.student_id = s.id AND a.date = ?
        WHERE c.status = 'active'
        GROUP BY c.id
        ORDER BY c.class_name, c.section
        """, (today_str,))
        class_summary = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
        SELECT s.id, s.name, c.class_name, c.section,
               COUNT(a.id) as total_days,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_days
        FROM students s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN attendance a ON s.id = a.student_id
        WHERE s.status = 'active'
        GROUP BY s.id
        HAVING total_days > 5 AND (CAST(present_days AS FLOAT) / total_days * 100) < 75.0
        """)
        low_att_students = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'role': role,
            'stats': {
                'total_schools': total_schools,
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_classes': total_classes,
                'today_present': today_present,
                'today_absent': today_absent,
                'today_late': today_late,
                'low_attendance_count': len(low_att_students)
            },
            'monthly_stats': monthly_stats,
            'recent_attendance': recent_attendance,
            'class_summary': class_summary,
            'low_attendance_students': low_att_students
        })

    elif role == 'teacher':
        cursor.execute("SELECT id FROM teachers WHERE user_id = ?", (user['id'],))
        t_row = cursor.fetchone()
        teacher_id = t_row['id'] if t_row else None

        cursor.execute("""
        SELECT c.*, COUNT(s.id) as student_count 
        FROM classes c
        LEFT JOIN students s ON s.class_id = c.id AND s.status = 'active'
        WHERE c.teacher_id = ? OR ? IS NULL
        GROUP BY c.id
        """, (teacher_id, teacher_id))
        assigned_classes = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
        SELECT COUNT(DISTINCT class_id) as marked_count 
        FROM attendance 
        WHERE date = ? AND (teacher_id = ? OR ? IS NULL)
        """, (today_str, teacher_id, teacher_id))
        today_marked_classes = cursor.fetchone()['marked_count']

        cursor.execute("""
        SELECT a.id, a.date, a.time, a.status, a.remarks, 
               s.name as student_name, s.roll_number,
               c.class_name, c.section
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN classes c ON a.class_id = c.id
        WHERE (a.teacher_id = ? OR ? IS NULL)
        ORDER BY a.date DESC, a.time DESC
        LIMIT 10
        """, (teacher_id, teacher_id))
        recent_attendance = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'role': role,
            'stats': {
                'assigned_classes_count': len(assigned_classes),
                'today_marked_classes': today_marked_classes,
                'total_students': sum(c['student_count'] for c in assigned_classes)
            },
            'assigned_classes': assigned_classes,
            'recent_attendance': recent_attendance
        })

    elif role == 'student':
        cursor.execute("""
        SELECT s.*, c.class_name, c.section, c.academic_year, t.name as class_teacher_name
        FROM students s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON c.teacher_id = t.id
        WHERE s.user_id = ?
        """, (user['id'],))
        student = cursor.fetchone()

        if not student:
            conn.close()
            return jsonify({'success': False, 'message': 'Student record not found.'}), 404

        sid = student['id']
        cursor.execute("""
        SELECT COUNT(*) as total_days, 
               SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days, 
               SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days, 
               SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days 
        FROM attendance WHERE student_id = ?
        """, (sid,))
        stats_row = cursor.fetchone()
        tot = stats_row['total_days'] or 0
        prs = stats_row['present_days'] or 0
        abs_cnt = stats_row['absent_days'] or 0
        lte = stats_row['late_days'] or 0
        pct = round((prs / tot * 100), 1) if tot > 0 else 0

        cursor.execute("SELECT status, time, remarks FROM attendance WHERE student_id = ? AND date = ?", (sid, today_str))
        today_row = cursor.fetchone()

        cursor.execute("""
        SELECT a.date, a.time, a.status, a.remarks, sub.subject_name
        FROM attendance a
        LEFT JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
        LIMIT 15
        """, (sid,))
        history = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'role': role,
            'student_profile': dict(student),
            'stats': {
                'total_working_days': tot,
                'present_days': prs,
                'absent_days': abs_cnt,
                'late_days': lte,
                'attendance_percentage': pct,
                'today_status': today_row['status'] if today_row else 'Not Marked Yet',
                'today_time': today_row['time'] if today_row else None
            },
            'recent_history': history
        })

    elif role == 'parent':
        cursor.execute("SELECT * FROM parents WHERE user_id = ?", (user['id'],))
        parent = cursor.fetchone()

        if not parent:
            conn.close()
            return jsonify({'success': False, 'message': 'Parent profile not found.'}), 404

        cursor.execute("""
        SELECT s.*, c.class_name, c.section, c.academic_year
        FROM students s
        JOIN classes c ON s.class_id = c.id
        WHERE s.parent_id = ?
        """, (parent['id'],))
        children = [dict(r) for r in cursor.fetchall()]

        children_stats = []
        for ch in children:
            sid = ch['id']
            cursor.execute("""
            SELECT COUNT(*) as total_days, 
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days, 
                   SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days, 
                   SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days 
            FROM attendance WHERE student_id = ?
            """, (sid,))
            s_row = cursor.fetchone()
            tot = s_row['total_days'] or 0
            prs = s_row['present_days'] or 0
            abs_c = s_row['absent_days'] or 0
            lte = s_row['late_days'] or 0
            pct = round((prs / tot * 100), 1) if tot > 0 else 0

            cursor.execute("SELECT status, time, remarks FROM attendance WHERE student_id = ? AND date = ?", (sid, today_str))
            t_row = cursor.fetchone()

            cursor.execute("SELECT date, time, status, remarks FROM attendance WHERE student_id = ? ORDER BY date DESC LIMIT 10", (sid,))
            recent = [dict(r) for r in cursor.fetchall()]

            children_stats.append({
                'child': ch,
                'stats': {
                    'total_working_days': tot,
                    'present_days': prs,
                    'absent_days': abs_c,
                    'late_days': lte,
                    'attendance_percentage': pct,
                    'today_status': t_row['status'] if t_row else 'Not Marked Yet',
                    'today_time': t_row['time'] if t_row else None
                },
                'recent_history': recent
            })

        conn.close()
        return jsonify({
            'success': True,
            'role': role,
            'parent_profile': dict(parent),
            'children': children_stats
        })

    conn.close()
    return jsonify({'success': False, 'message': 'Unknown user role.'}), 400
