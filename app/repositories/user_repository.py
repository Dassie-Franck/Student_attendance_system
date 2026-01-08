from app.models.user import UserModel
from app.database.connDB import db
from werkzeug.security import generate_password_hash


class UserRepository:

    @staticmethod
    def get_all():
        return UserModel.query.all()

    @staticmethod
    def find_by_email(email):
        return UserModel.query.filter_by(email=email).first()

    @staticmethod
    def get_by_id(user_id):
        return UserModel.query.get(user_id)

    @staticmethod
    def create_user(data):
        """
        data: dict {nom, prenom, email, password, role, filiere}
        """
        try:
            # Vérifier si l'utilisateur existe déjà
            existing_user = UserRepository.find_by_email(data['email'])
            if existing_user:
                raise Exception("Un utilisateur avec cet email existe déjà")

            hashed_password = generate_password_hash(data['password'])

            user = UserModel(
                nom=data['nom'],
                prenom=data['prenom'],
                email=data['email'],
                mot_de_passe=hashed_password,
                role=data['role'],
                filiere=data.get('filiere', '')
            )
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_user(user, data):
        """
        user: instance UserModel
        data: dict avec les champs à mettre à jour
        """
        try:
            # Vérifier si l'email est changé et s'il existe déjà
            if 'email' in data and data['email'] != user.email:
                existing = UserRepository.find_by_email(data['email'])
                if existing and existing.id != user.id:
                    raise Exception("Un utilisateur avec cet email existe déjà")

            user.nom = data.get('nom', user.nom)
            user.prenom = data.get('prenom', user.prenom)
            user.email = data.get('email', user.email)
            user.role = data.get('role', user.role)
            user.filiere = data.get('filiere', user.filiere)

            # Mettre à jour le mot de passe seulement s'il est fourni
            if 'password' in data and data['password']:
                user.mot_de_passe = generate_password_hash(data['password'])

            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_user(user):
        """
        user: instance UserModel
        """
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e