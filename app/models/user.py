from app.models.enum import UserRole
from app.database.connDB import db

class UserModel(db.Model):
    __tablename__ = "user"  # Nom exact de la  table MySQL

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe= db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole.HEAD.value, UserRole.ENSEIGNANT.value, UserRole.DELEGUE.value), nullable=False)
    filiere = db.Column(db.String(50))
