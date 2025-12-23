
from flask import Flask
from app.config import Config
from app.database.connDB import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation DB
    db.init_app(app)

    from app.controllers import users_controller
    app.register_blueprint(users_controller.bp)

    from app.auth.auth_controller import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.controllers.course_controller import cours_bp
    app.register_blueprint(cours_bp)

    from app.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp,url_prefix="/dashboard")

    from app.controllers.student_controller import student_bp
    app.register_blueprint(student_bp)

    return app

