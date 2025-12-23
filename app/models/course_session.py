from app.database.connDB import db
from app.models.enum import CourSession

class CoursSessionModel(db.Model):
    __tablename__ = "cours_session"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)

    seance = db.Column(
        db.Enum(CourSession),
        nullable=False
    )

    cours_id = db.Column(
        db.Integer,
        db.ForeignKey("cours.id"),
        nullable=False
    )
