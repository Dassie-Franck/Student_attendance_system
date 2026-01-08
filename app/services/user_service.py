from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.enum import UserRole


class UserService:

    @staticmethod
    def create(data):
        """
        data: dict {nom, prenom, email, password, role, filiere}
        """
        # Normalisez le rôle selon vos valeurs d'Enum
        role = data.get('role', '')
        if role.upper() == 'HEAD':
            data['role'] = UserRole.HEAD.value  # "respoFiliere"
        elif role.upper() == 'ENSEIGNANT':
            data['role'] = UserRole.ENSEIGNANT.value  # "ensg"
        elif role.upper() == 'DELEGUE':
            data['role'] = UserRole.DELEGUE.value  # "delegue"
        else:
            # Si c'est déjà la valeur française, conservez-la
            if role not in [UserRole.HEAD.value, UserRole.ENSEIGNANT.value, UserRole.DELEGUE.value]:
                raise Exception(f"Rôle invalide: {role}")

        return UserRepository.create_user(data)

    @staticmethod
    def get_all():
        return UserRepository.get_all()

    @staticmethod
    def get_by_id(user_id):
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def update(user, data):
        # Gérer la conversion du rôle si présent
        if 'role' in data:
            role = data['role']
            if role.upper() == 'HEAD':
                data['role'] = UserRole.HEAD.value
            elif role.upper() == 'ENSEIGNANT':
                data['role'] = UserRole.ENSEIGNANT.value
            elif role.upper() == 'DELEGUE':
                data['role'] = UserRole.DELEGUE.value
        return UserRepository.update_user(user, data)

    @staticmethod
    def delete(user):
        return UserRepository.delete_user(user)

    # Rôles - utiliser les valeurs correctes
    @staticmethod
    def is_responsable(user: UserModel):
        return user.role == UserRole.HEAD.value  # "respoFiliere"

    @staticmethod
    def is_enseignant(user: UserModel):
        return user.role == UserRole.ENSEIGNANT.value  # "ensg"

    @staticmethod
    def is_delegue(user: UserModel):
        return user.role == UserRole.DELEGUE.value  # "delegue"

    # Droits métier
    @staticmethod
    def can_crud_user(user: UserModel):
        return UserService.is_responsable(user)

    @staticmethod
    def can_create_course(user: UserModel):
        return UserService.is_responsable(user) or UserService.is_enseignant(user)

    @staticmethod
    def can_take_attendance(user: UserModel):
        return UserService.is_enseignant(user) or UserService.is_delegue(user)

    # Login
    @staticmethod
    def login(email, password):
        user = UserRepository.find_by_email(email)
        if not user:
            raise Exception("Utilisateur inexistant")
        if not check_password_hash(user.mot_de_passe, password):
            raise Exception("Mot de passe incorrect")
        return user

    @staticmethod
    def get_role_display(role_value):
        """
        Convertit la valeur stockée en nom d'affichage
        """
        if role_value == UserRole.HEAD.value:
            return "Responsable"
        elif role_value == UserRole.ENSEIGNANT.value:
            return "Enseignant"
        elif role_value == UserRole.DELEGUE.value:
            return "delegue"
        return role_value