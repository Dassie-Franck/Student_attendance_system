# app/models/course.py
from app.database.connDB import db


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

    # Propriété pour accéder aux sessions
    @property
    def sessions(self):
        """Retourne les sessions du cours"""
        from app.models.course_session import CoursSessionModel
        if not hasattr(self, '_sessions'):
            self._sessions = CoursSessionModel.query.filter_by(cours_id=self.id).all()
        return self._sessions

    @sessions.setter
    def sessions(self, value):
        """Setter pour les sessions"""
        self._sessions = value

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'user_id': self.user_id,
            'filiere': self.filiere,
            'semestre': self.semestre,
            'sessions': [{
                'id': s.id,
                'date': s.date.isoformat() if s.date else None,
                'seance': s.seance
            } for s in self.sessions]
        }