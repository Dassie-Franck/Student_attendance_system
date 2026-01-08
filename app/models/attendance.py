# app/models/attendance.py
from app.database.connDB import db
from datetime import datetime
from sqlalchemy.orm import relationship


class PresenceModel(db.Model):
    __tablename__ = 'presence'

    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey('etudiant.id'), nullable=False)
    cours_session_id = db.Column(db.Integer, db.ForeignKey('cours_session.id'), nullable=False)
    statut = db.Column(db.Enum('P', 'A'), nullable=False)
    date_enregistrement = db.Column(db.TIMESTAMP, default=datetime.now)
    date_mise_a_jour = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    # Relations
    etudiant = relationship('EtudiantModel', backref='presences', lazy='joined')
    session = relationship('CoursSessionModel', backref='presences', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'etudiant_id': self.etudiant_id,
            'cours_session_id': self.cours_session_id,
            'statut': self.statut,
            'date_enregistrement': self.date_enregistrement.isoformat() if self.date_enregistrement else None,
            'date_mise_a_jour': self.date_mise_a_jour.isoformat() if self.date_mise_a_jour else None
        }