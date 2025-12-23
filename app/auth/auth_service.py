from flask import session
from app.services.user_service import UserService
from app.models.enum import UserRole

class AuthService:

    @staticmethod
    def login(email, password):
        user = UserService.login(email, password)

        # Sécurité : les étudiants ne peuvent pas se connecter
        if user.role not in [
            UserRole.HEAD.value,
            UserRole.ENSEIGNANT.value,
            UserRole.DELEGUE.value
        ]:
            raise Exception("Accès interdit")

        session["user_id"] = user.id
        session["role"] = user.role
        session["nom"] = user.nom

        return user

    @staticmethod
    def logout():
        session.clear()

    @staticmethod
    def is_authenticated():
        return "user_id" in session
