# app/repositories/user_repository.py
from app.models.user import UserModel
from app.database.connDB import db

class UserRepository:

    @staticmethod
    def get_all():
        return UserModel.query.all()

    @staticmethod
    def find_by_email(email):
        return UserModel.query.filter_by(email=email).first()

    @staticmethod
    def find_by_id(user_id):
        return UserModel.query.get(user_id)

    @staticmethod
    def create(nom, prenom, email, password, role,filiere):
        user = UserModel(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=password,
            role=role,
            filiere=filiere,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user: UserModel):
        db.session.commit()
        return user

    @staticmethod
    def delete(user: UserModel):
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def get_by_id(user_id):
        return UserModel.query.get(user_id)