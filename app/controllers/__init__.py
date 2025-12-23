from flask import Flask
from .student_controller import student_bp

def register_blueprints(app: Flask):
    app.register_blueprint(student_bp)
