import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from backend.config import Config
from backend.database import get_db

def generate_token(user_data):
    payload = {
        'id': user_data['id'],
        'username': user_data['username'],
        'role': user_data['role'],
        'name': user_data['name'],
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header
        
        if not token:
            return jsonify({'success': False, 'message': 'Authentication token is missing.'}), 401
        
        try:
            data = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (data['id'],))
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return jsonify({'success': False, 'message': 'User no longer exists.'}), 401
            
            if user['status'] != 'active':
                return jsonify({'success': False, 'message': 'Your account is inactive. Please contact the administrator.'}), 403
            
            request.current_user = dict(user)
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid authentication token.'}), 401
            
        return f(*args, **kwargs)
    return decorated

def roles_accepted(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user') or not request.current_user:
                return jsonify({'success': False, 'message': 'Unauthorized access.'}), 401
            
            user_role = request.current_user.get('role')
            if user_role not in allowed_roles and 'admin' not in allowed_roles and user_role != 'admin':
                return jsonify({'success': False, 'message': 'You do not have permission to perform this action.'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
