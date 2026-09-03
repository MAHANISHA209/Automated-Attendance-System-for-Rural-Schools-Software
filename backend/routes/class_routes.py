from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.middleware.auth import token_required, roles_accepted

class_bp = Blueprint('classes', __name__, url_prefix='/api/classes')

@class_bp.route('', methods=['GET'])
@token_required
def get_classes():
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT c.*, t.name as class_teacher_name, t.phone as teacher_phone,
           COUNT(s.id) as student_count
    FROM classes c
    LEFT JOIN teachers t ON c.teacher_id = t.id
    LEFT JOIN students s ON s.class_id = c.id AND s.status = 'active'
    GROUP BY c.id
    ORDER BY c.class_name, c.section
    """
    cursor.execute(query)
    classes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'classes': classes, 'total': len(classes)})

@class_bp.route('/<id>', methods=['GET'])
@token_required
def get_class_detail(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, t.name as class_teacher_name, t.phone as teacher_phone
    FROM classes c
    LEFT JOIN teachers t ON c.teacher_id = t.id
    WHERE c.id = ?
    """, (id,))
    class_row = cursor.fetchone()
    if not class_row:
        conn.close()
        return jsonify({'success': False, 'message': 'Class not found.'}), 404

    cursor.execute('SELECT * FROM students WHERE class_id = ? ORDER BY roll_number', (id,))
    students = [dict(r) for r in cursor.fetchall()]

    cursor.execute('SELECT * FROM subjects WHERE class_id = ?', (id,))
    subjects = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({'success': True, 'class': dict(class_row), 'students': students, 'subjects': subjects})

@class_bp.route('', methods=['POST'])
@token_required
@roles_accepted('admin', 'principal')
def add_class():
    data = request.get_json() or {}
    class_name = data.get('class_name', '').strip()
    section = data.get('section', '').strip() or 'A'
    teacher_id = data.get('teacher_id')
    academic_year = data.get('academic_year', '2026-2027').strip()
    room_number = data.get('room_number', '').strip()
    status = data.get('status', 'active')

    if not class_name:
        return jsonify({'success': False, 'message': 'Class name is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO classes (class_name, section, teacher_id, academic_year, room_number, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (class_name, section, teacher_id, academic_year, room_number, status))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Class added successfully.'})
    except Exception:
        conn.close()
        return jsonify({'success': False, 'message': 'Class already exists for this section and year.'}), 400

@class_bp.route('/<id>', methods=['PUT'])
@token_required
@roles_accepted('admin', 'principal')
def update_class(id):
    data = request.get_json() or {}
    class_name = data.get('class_name', '').strip()
    section = data.get('section', '').strip()
    teacher_id = data.get('teacher_id')
    academic_year = data.get('academic_year', '2026-2027').strip()
    room_number = data.get('room_number', '').strip()
    status = data.get('status', 'active')

    if not class_name:
        return jsonify({'success': False, 'message': 'Class name is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE classes SET class_name = ?, section = ?, teacher_id = ?, academic_year = ?, room_number = ?, status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (class_name, section, teacher_id, academic_year, room_number, status, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Class updated successfully.'})

@class_bp.route('/<id>', methods=['DELETE'])
@token_required
@roles_accepted('admin', 'principal')
def delete_class(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM students WHERE class_id = ?', (id,))
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Cannot delete class containing students. Reassign students first.'}), 400

    cursor.execute('DELETE FROM classes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Class deleted successfully.'})
