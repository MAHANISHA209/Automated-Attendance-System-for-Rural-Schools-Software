import os
from flask import Flask, send_from_directory, jsonify
from backend.config import Config
from backend.database import init_db, seed_data

from backend.routes.auth_routes import auth_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.student_routes import student_bp
from backend.routes.teacher_routes import teacher_bp
from backend.routes.class_routes import class_bp
from backend.routes.attendance_routes import attendance_bp
from backend.routes.report_routes import report_bp
from backend.routes.notification_routes import notification_bp
from backend.routes.settings_routes import settings_bp
from backend.routes.export_routes import export_bp

def create_app():
    static_folder = os.path.join(os.path.dirname(__file__), 'backend', 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    app.config.from_object(Config)

    # Initialize and seed database if not exists
    init_db()
    seed_data()

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(class_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(export_bp)

    @app.route('/')
    def index():
        return send_from_directory(static_folder, 'index.html')

    @app.route('/health')
    def health():
        return jsonify({'status': 'online', 'system': 'Automated Attendance System for Rural Schools', 'version': '2.0.0'})

    @app.errorhandler(404)
    def not_found(e):
        return send_from_directory(static_folder, 'index.html')

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': 'An internal server error occurred.'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"================================================================")
    print(f" Green Valley Rural School - Automated Attendance System")
    print(f" Server running at http://127.0.0.1:{port}")
    print(f" Educational management visual banner loaded on login screen.")
    print(f"================================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
