# app/repositories/attendance_repository.py
from app.database.connDB import db
from app.models.attendance import PresenceModel
from app.models.student import EtudiantModel
from app.models.course_session import CoursSessionModel
from app.models.course import CoursModel
from sqlalchemy.exc import SQLAlchemyError
from datetime import date


class AttendanceRepository:

    @staticmethod
    def get_today_sessions_with_presence(user_id):
        """Récupère les sessions d'aujourd'hui avec présences"""
        try:
            today = date.today()
            sessions = (
                CoursSessionModel.query
                .join(CoursModel, CoursModel.id == CoursSessionModel.cours_id)
                .filter(
                    CoursSessionModel.date == today,
                    CoursModel.user_id == user_id
                )
                .options(
                    db.joinedload(CoursSessionModel.cours),
                    db.joinedload(CoursSessionModel.presences).joinedload(PresenceModel.etudiant)
                )
                .all()
            )
            return sessions
        except SQLAlchemyError as e:
            print(f"Erreur get_today_sessions_with_presence: {e}")
            return []

    @staticmethod
    def get_session_with_presence(session_id):
        """Récupère une session avec ses présences et les étudiants"""
        try:
            session = (
                CoursSessionModel.query
                .filter_by(id=session_id)
                .options(
                    db.joinedload(CoursSessionModel.cours),
                    db.joinedload(CoursSessionModel.presences).joinedload(PresenceModel.etudiant)  # MODIFIÉ
                )
                .first()
            )
            return session
        except SQLAlchemyError as e:
            print(f"Erreur get_session_with_presence: {e}")
            return None

    @staticmethod
    def get_etudiants_by_filiere(filiere):
        """Récupère les étudiants d'une filière"""
        try:
            etudiants = EtudiantModel.query.filter_by(filiere=filiere).all()
            print(f"DEBUG: {len(etudiants)} étudiants trouvés pour filière '{filiere}'")
            return etudiants
        except SQLAlchemyError as e:
            print(f"Erreur get_etudiants_by_filiere: {e}")
            return []

    @staticmethod
    def create_or_update_presence(etudiant_id, cours_session_id, statut):
        """Crée ou met à jour une présence"""
        try:
            presence = PresenceModel.query.filter_by(
                etudiant_id=etudiant_id,
                cours_session_id=cours_session_id
            ).first()

            if presence:
                presence.statut = statut
                print(f"DEBUG: Présence mise à jour - ID: {presence.id}, Statut: {statut}")
            else:
                presence = PresenceModel(
                    etudiant_id=etudiant_id,
                    cours_session_id=cours_session_id,
                    statut=statut
                )
                db.session.add(presence)
                print(f"DEBUG: Nouvelle présence créée - Étudiant: {etudiant_id}, Session: {cours_session_id}")

            db.session.commit()
            return presence
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Erreur create_or_update_presence: {e}")
            raise

    @staticmethod
    def get_presences_by_session(session_id):
        """Récupère toutes les présences d'une session"""
        try:
            presences = (
                PresenceModel.query
                .filter_by(cours_session_id=session_id)
                .options(db.joinedload(PresenceModel.etudiant))
                .all()
            )
            print(f"DEBUG: {len(presences)} présences trouvées pour session {session_id}")
            return presences
        except SQLAlchemyError as e:
            print(f"Erreur get_presences_by_session: {e}")
            return []