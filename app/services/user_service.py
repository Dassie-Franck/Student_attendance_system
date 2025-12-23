from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.enum import UserRole

class UserService:

    @staticmethod
    def create_user(nom, prenom, email, password, role, filiere):
        hashed_password = generate_password_hash(password)
        return UserRepository.create(
            nom=nom,
            prenom=prenom,
            email=email,
            password=hashed_password,
            role=role,   # stocke la valeur exacte du rôle
            filiere=filiere,
        )

    # Rôles
    @staticmethod
    def is_responsable(user: UserModel):
        return user.role == UserRole.HEAD.value

    @staticmethod
    def is_enseignant(user: UserModel):
        return user.role == UserRole.ENSEIGNANT.value

    @staticmethod
    def is_delegue(user: UserModel):
        return user.role == UserRole.DELEGUE.value

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
    def get_user_by_id(user_id):
        return UserRepository.get_by_id(user_id)

