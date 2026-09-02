from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.middleware.auth import token_required, roles_accepted

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()

    settings = {r['key']: r['value'] for r in rows}
    return jsonify({'success': True, 'settings': settings})

@settings_bp.route('', methods=['POST'])
@token_required
@roles_accepted('admin', 'principal')
def update_settings():
    data = request.get_json() or {}
    conn = get_db()
    cursor = conn.cursor()

    for k, v in data.items():
        cursor.execute("""
        INSERT INTO settings (key, value, updated_at) 
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (k, str(v)))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'System settings updated successfully.'})

@settings_bp.route('/users', methods=['GET'])
@token_required
@roles_accepted('admin')
def get_users_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, username, role, phone, status, created_at FROM users ORDER BY role, name")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'users': users})

@settings_bp.route('/users/<id>/status', methods=['PUT'])
@token_required
@roles_accepted('admin')
def toggle_user_status(id):
    data = request.get_json() or {}
    status = data.get('status', 'active')

    if status not in ('active', 'inactive'):
        return jsonify({'success': False, 'message': 'Invalid status.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'User account status changed to {status}.'})
