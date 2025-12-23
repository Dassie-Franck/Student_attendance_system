# app/controllers/user_controller.py
from flask import Blueprint, request, jsonify
from app.services.user_service import UserService

bp = Blueprint("user", __name__, url_prefix="/users")

def get_current_user():
    from app.repositories.user_repository import UserRepository
    email = request.headers.get("X-User-Email")
    if not email:
        raise Exception("Utilisateur non connecté")
    return UserRepository.find_by_email(email)

@bp.route("/add", methods=["POST"])
def add_user():
    try:
        current_user = get_current_user()
        if not UserService.can_crud_user(current_user):
            return jsonify({"error": "Seul le responsable peut créer un compte"}), 403

        data = request.get_json()
        user = UserService.create_user(
            nom=data["nom"],
            prenom=data["prenom"],
            email=data["email"],
            password=data["password"],
            role=data["role"],
            filiere=data["filiere"],
        )
        return jsonify({"message": f"Utilisateur {user.nom} créé "})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
