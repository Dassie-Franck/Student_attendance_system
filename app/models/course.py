from app.database.connDB import db
from app.models.enum import CourSession


class CoursModel(db.Model):
    __tablename__ = "cours"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    filiere = db.Column(db.String(100), nullable=False)
    semestre = db.Column(db.String(20), nullable=False)

    # Relation ORM
    sessions = db.relationship(
        "CoursSessionModel",
        backref="cours",
        cascade="all, delete-orphan",
        lazy=True
    )


class CoursSessionModel(db.Model):
    __tablename__ = "cours_session"

    id = db.Column(db.Integer, primary_key=True)
    cours_id = db.Column(
        db.Integer,
        db.ForeignKey("cours.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    seance = db.Column(
        db.Enum("1", "2", name="seance_enum"),
        nullable=False
    )
