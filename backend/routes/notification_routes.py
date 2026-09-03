from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.middleware.auth import token_required, roles_accepted

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notification_bp.route('', methods=['GET'])
@token_required
def get_notifications():
    user_id = request.current_user['id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM notifications 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT 30
    """, (user_id,))
    notifications = [dict(r) for r in cursor.fetchall()]
    unread_count = sum(1 for n in notifications if not n['is_read'])
    conn.close()

    return jsonify({
        'success': True,
        'notifications': notifications,
        'unread_count': unread_count
    })

@notification_bp.route('/<id>/read', methods=['PUT'])
@token_required
def mark_notification_read(id):
    user_id = request.current_user['id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Marked as read.'})

@notification_bp.route('/read-all', methods=['PUT'])
@token_required
def mark_all_read():
    user_id = request.current_user['id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'All notifications marked as read.'})
