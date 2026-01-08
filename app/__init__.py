# app/__init__.py
from flask import Flask
from app.config import Config
from app.database.connDB import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation DB
    db.init_app(app)

    # Enregistrement des blueprints (dans l'ordre logique)

    # 1. Authentification
    from app.auth.auth_controller import bp as auth_bp
    app.register_blueprint(auth_bp)

    # 2. Dashboard
    from app.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    # 3. Utilisateurs
    from app.controllers import users_controller
    app.register_blueprint(users_controller.bp)

    # 4. Étudiants
    from app.controllers.student_controller import student_bp
    app.register_blueprint(student_bp)

    # 5. Cours
    from app.controllers.course_controller import cours_bp
    app.register_blueprint(cours_bp)


    # # 6. Attendance (NOUVEAU - à ajouter)
    # from app.controllers.scan_controller import scan_bp
    # app.register_blueprint(attendance_bp, url_prefix="/attendance")

    # 7. Scan
    from app.controllers.scan_controller import scan_bp
    app.register_blueprint(scan_bp, url_prefix='/scan')

    from app.controllers.attendance_controller import attendance_bp
    app.register_blueprint(attendance_bp, url_prefix='/attendance')

    return app