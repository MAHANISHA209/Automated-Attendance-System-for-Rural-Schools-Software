from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from backend.database import get_db, Config
from backend.middleware.auth import token_required, roles_accepted

teacher_bp = Blueprint('teachers', __name__, url_prefix='/api/teachers')

@teacher_bp.route('', methods=['GET'])
@token_required
def get_teachers():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    subject = request.args.get('subject', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT t.*, c.class_name, c.section as assigned_section, c.id as assigned_class_id
    FROM teachers t
    LEFT JOIN classes c ON c.teacher_id = t.id
    WHERE 1=1
    """
    params = []

    if search:
        query += " AND (t.name LIKE ? OR t.teacher_id LIKE ? OR t.email LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if status:
        query += " AND t.status = ?"
        params.append(status)

    if subject:
        query += " AND t.subject LIKE ?"
        params.append(f"%{subject}%")

    query += " ORDER BY t.name"
    cursor.execute(query, params)
    teachers = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({'success': True, 'teachers': teachers, 'total': len(teachers)})

@teacher_bp.route('/<id>', methods=['GET'])
@token_required
def get_teacher(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers WHERE id = ?", (id,))
    t = cursor.fetchone()
    if not t:
        conn.close()
        return jsonify({'success': False, 'message': 'Teacher not found.'}), 404

    cursor.execute("SELECT * FROM classes WHERE teacher_id = ?", (id,))
    classes = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT s.*, c.class_name, c.section FROM subjects s JOIN classes c ON s.class_id = c.id WHERE s.teacher_id = ?", (id,))
    subjects = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({'success': True, 'teacher': dict(t), 'classes': classes, 'subjects': subjects})

@teacher_bp.route('', methods=['POST'])
@token_required
@roles_accepted('admin', 'principal')
def add_teacher():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    gender = data.get('gender', 'Male').strip()
    qualification = data.get('qualification', '').strip()
    subject = data.get('subject', '').strip()
    address = data.get('address', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', 'Teacher@123').strip()
    status = data.get('status', 'active')

    if not name or not email or not phone:
        return jsonify({'success': False, 'message': 'Name, Email, and Phone are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    if not username:
        username = email.split('@')[0].replace('.', '_')

    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    ex_u = cursor.fetchone()
    if ex_u:
        user_id = ex_u['id']
    else:
        pw_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (name, email, username, password, role, phone, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'teacher', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (name, email, username, pw_hash, phone, status))
        user_id = cursor.lastrowid

    cursor.execute("SELECT MAX(id) as max_id FROM teachers")
    max_id = (cursor.fetchone()['max_id'] or 0) + 1
    teacher_id = f"TCH-{max_id:03d}"

    cursor.execute("""
    INSERT INTO teachers (teacher_id, name, email, phone, gender, qualification, subject, address, status, user_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (teacher_id, name, email, phone, gender, qualification, subject, address, status, user_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Teacher added successfully.', 'teacher_id': teacher_id})

@teacher_bp.route('/<id>', methods=['PUT'])
@token_required
@roles_accepted('admin', 'principal')
def update_teacher(id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    gender = data.get('gender', 'Male').strip()
    qualification = data.get('qualification', '').strip()
    subject = data.get('subject', '').strip()
    address = data.get('address', '').strip()
    status = data.get('status', 'active')

    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE teachers SET name = ?, email = ?, phone = ?, gender = ?, qualification = ?, subject = ?, address = ?, status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (name, email, phone, gender, qualification, subject, address, status, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Teacher updated successfully.'})

@teacher_bp.route('/<id>', methods=['DELETE'])
@token_required
@roles_accepted('admin', 'principal')
def delete_teacher(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teachers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Teacher deleted successfully.'})
