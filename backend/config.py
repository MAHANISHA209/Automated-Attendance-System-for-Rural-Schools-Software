import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rural-school-attendance-secret-key-2026')
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-attendance-auth-secret-key-2026')
    JWT_EXPIRATION_HOURS = 24
    DB_PATH = os.path.join(PROJECT_DIR, 'database', 'attendance.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DEFAULT_LOW_ATTENDANCE_THRESHOLD = 75.0
