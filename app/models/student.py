from app.database.connDB import db

class EtudiantModel(db.Model):
    __tablename__ = "etudiant"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    matricule = db.Column(db.String(20), nullable=False, unique=True)
    filiere = db.Column(db.String(100), nullable=False)
    annee = db.Column(db.String(20), nullable=False)

    profil = db.relationship("ProfilModel", backref="etudiant", uselist=False, cascade="all, delete-orphan")


class ProfilModel(db.Model):
    __tablename__ = "profil"
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    photo_avant = db.Column(db.String(255), nullable=False)
    photo_gauche = db.Column(db.String(255), nullable=False)
    photo_droite = db.Column(db.String(255), nullable=False)


