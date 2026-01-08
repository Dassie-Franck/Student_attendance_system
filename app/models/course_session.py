# app/models/course_session.py
from app.database.connDB import db
from sqlalchemy.orm import relationship


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

    # Relation - gardez seulement celle-ci
    cours = relationship(
        'CoursModel',
        backref='session_objects',  # Changez le nom pour éviter le conflit
        lazy='joined'
    )

    def to_dict(self):
        cours_dict = None
        if hasattr(self, 'cours') and self.cours:
            cours_dict = {
                'id': self.cours.id,
                'nom': self.cours.nom,
                'filiere': self.cours.filiere,
                'semestre': self.cours.semestre
            }

        return {
            'id': self.id,
            'cours_id': self.cours_id,
            'date': self.date.isoformat() if self.date else None,
            'seance': self.seance,
            'cours': cours_dict,
            'display_text': f"{self.date.strftime('%d/%m/%Y')} - Séance {self.seance}"
        }