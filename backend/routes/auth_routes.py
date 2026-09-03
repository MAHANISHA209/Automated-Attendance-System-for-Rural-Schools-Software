from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database import get_db
from backend.middleware.auth import generate_token, token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username:
        return jsonify({'success': False, 'message': 'Please enter your username or email.'}), 400
    
    if not password:
        return jsonify({'success': False, 'message': 'Please enter your password.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username))
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user['password'], password):
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401

    if user['status'] != 'active':
        conn.close()
        return jsonify({'success': False, 'message': 'Your account is inactive. Please contact the administrator.'}), 403

    user_dict = dict(user)
    token = generate_token(user_dict)
    
    role_info = {}
    if user['role'] == 'teacher':
        cursor.execute('SELECT * FROM teachers WHERE user_id = ?', (user['id'],))
        t = cursor.fetchone()
        if t: role_info['teacher'] = dict(t)
    elif user['role'] == 'student':
        cursor.execute('SELECT s.*, c.class_name, c.section FROM students s JOIN classes c ON s.class_id = c.id WHERE s.user_id = ?', (user['id'],))
        s = cursor.fetchone()
        if s: role_info['student'] = dict(s)
    elif user['role'] == 'parent':
        cursor.execute('SELECT * FROM parents WHERE user_id = ?', (user['id'],))
        p = cursor.fetchone()
        if p:
            role_info['parent'] = dict(p)
            cursor.execute('SELECT s.*, c.class_name, c.section FROM students s JOIN classes c ON s.class_id = c.id WHERE s.parent_id = ?', (p['id'],))
            role_info['children'] = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'phone': user['phone'],
            'avatar': user['avatar']
        },
        'role_info': role_info
    })

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    user = request.current_user
    conn = get_db()
    cursor = conn.cursor()
    
    role_info = {}
    if user['role'] == 'teacher':
        cursor.execute('SELECT * FROM teachers WHERE user_id = ?', (user['id'],))
        t = cursor.fetchone()
        if t: role_info['teacher'] = dict(t)
    elif user['role'] == 'student':
        cursor.execute('SELECT s.*, c.class_name, c.section FROM students s JOIN classes c ON s.class_id = c.id WHERE s.user_id = ?', (user['id'],))
        s = cursor.fetchone()
        if s: role_info['student'] = dict(s)
    elif user['role'] == 'parent':
        cursor.execute('SELECT * FROM parents WHERE user_id = ?', (user['id'],))
        p = cursor.fetchone()
        if p:
            role_info['parent'] = dict(p)
            cursor.execute('SELECT s.*, c.class_name, c.section FROM students s JOIN classes c ON s.class_id = c.id WHERE s.parent_id = ?', (p['id'],))
            role_info['children'] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({
        'success': True,
        'user': user,
        'role_info': role_info
    })

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    data = request.get_json() or {}
    user_id = request.current_user['id']
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    avatar = data.get('avatar', '').strip()

    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET name = ?, phone = ?, avatar = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (name, phone, avatar, user_id))
    
    if request.current_user['role'] == 'teacher':
        cursor.execute('UPDATE teachers SET name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (name, phone, user_id))
    elif request.current_user['role'] == 'parent':
        cursor.execute('UPDATE parents SET name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (name, phone, user_id))
    elif request.current_user['role'] == 'student':
        cursor.execute('UPDATE students SET name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (name, phone, user_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Profile updated successfully.'})

@auth_bp.route('/change-password', methods=['PUT'])
@token_required
def change_password():
    data = request.get_json() or {}
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()

    if not old_password or not new_password:
        return jsonify({'success': False, 'message': 'Both old and new passwords are required.'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters long.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE id = ?', (request.current_user['id'],))
    row = cursor.fetchone()

    if not row or not check_password_hash(row['password'], old_password):
        conn.close()
        return jsonify({'success': False, 'message': 'Current password does not match.'}), 400

    hashed = generate_password_hash(new_password)
    cursor.execute('UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (hashed, request.current_user['id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Password changed successfully.'})

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    if not identifier:
        return jsonify({'success': False, 'message': 'Please enter your username or registered email.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': 'No account found with provided credentials.'}), 404

    return jsonify({
        'success': True,
        'message': f'Password reset link generated for {user["email"]}. Demo accounts can reset password in Settings.'
    })
