# app/services/course_service.py
from sqlalchemy.orm import joinedload
from datetime import datetime, date
from app.models.course import CoursModel
from app.models.course_session import CoursSessionModel
from app.database.connDB import db
from app.models.user import UserModel


class CoursService:

    @staticmethod
    def get_user_courses(user_id):
        # Utilisez 'session_objects' au lieu de 'sessions' si c'est le nom que vous avez utilisé
        # OU utilisez une jointure explicite
        return (
            CoursModel.query
            .filter_by(user_id=user_id)
            .order_by(CoursModel.id.desc())
            .all()
        )

    @staticmethod
    def get_course(course_id, user_id):
        cours = CoursModel.query.filter_by(
            id=course_id,
            user_id=user_id
        ).first()

        if cours:
            # Chargez les sessions séparément si nécessaire
            cours.sessions_list = CoursSessionModel.query.filter_by(cours_id=course_id).all()

        return cours

    @staticmethod
    def create_course(user_id, nom, filiere, semestre, sessions):
        cours = CoursModel(
            user_id=user_id,
            nom=nom,
            filiere=filiere,
            semestre=semestre
        )
        db.session.add(cours)
        db.session.flush()

        for s in sessions:
            db.session.add(
                CoursSessionModel(
                    cours_id=cours.id,
                    date=datetime.strptime(s["date"], "%Y-%m-%d").date(),
                    seance=s["seance"]
                )
            )

        db.session.commit()
        return cours

    @staticmethod
    def update_course(course_id, user_id, nom, filiere, semestre, sessions):
        # Récupérer le cours
        cours = CoursModel.query.filter_by(id=course_id, user_id=user_id).first()
        if not cours:
            raise ValueError("Cours non trouvé")

        # Mettre à jour les infos de base
        cours.nom = nom
        cours.filiere = filiere
        cours.semestre = semestre

        # Supprimer les anciennes sessions
        CoursSessionModel.query.filter_by(cours_id=course_id).delete()

        # Ajouter les nouvelles sessions
        for s in sessions:
            db.session.add(
                CoursSessionModel(
                    cours_id=course_id,
                    date=datetime.strptime(s["date"], "%Y-%m-%d").date(),
                    seance=s["seance"]
                )
            )

        db.session.commit()
        return cours

    @staticmethod
    def delete_course(course_id, user_id):
        cours = CoursModel.query.filter_by(id=course_id, user_id=user_id).first()
        if not cours:
            raise ValueError("Cours non trouvé")

        db.session.delete(cours)
        db.session.commit()
        return True

    @staticmethod
    def get_today_courses_by_filiere(user_id, filiere):
        today = date.today()

        # Récupérer les cours avec leurs sessions
        cours_list = CoursModel.query.filter_by(
            user_id=user_id,
            filiere=filiere
        ).all()

        today_courses = []
        for cours in cours_list:
            # Récupérer les sessions d'aujourd'hui pour ce cours
            sessions_today = CoursSessionModel.query.filter_by(
                cours_id=cours.id,
                date=today
            ).all()

            if sessions_today:
                today_courses.append({
                    "id": cours.id,
                    "nom": cours.nom,
                    "filiere": cours.filiere,
                    "semestre": cours.semestre,
                    "sessions": [{
                        "date": s.date,
                        "seance": s.seance
                    } for s in sessions_today]
                })

        return today_courses

    @staticmethod
    def get_available_filieres_for_today(user_id):
        today = date.today()

        # Utilisez une sous-requête ou une jointure explicite
        result = (
            db.session.query(CoursModel.filiere)
            .distinct()
            .join(CoursSessionModel, CoursSessionModel.cours_id == CoursModel.id)
            .filter(
                CoursModel.user_id == user_id,
                CoursSessionModel.date == today
            )
            .all()
        )

        return [row[0] for row in result]

    @staticmethod
    def get_all_cours():
        """Récupère tous les cours"""
        try:
            return CoursModel.query \
                .join(UserModel, CoursModel.user_id == UserModel.id) \
                .order_by(CoursModel.nom) \
                .all()
        except:
            return []

    @staticmethod
    def get_cours_by_filiere(filiere):
        """Récupère les cours par filière"""
        try:
            return CoursModel.query \
                .join(UserModel, CoursModel.user_id == UserModel.id) \
                .filter(CoursModel.filiere == filiere) \
                .order_by(CoursModel.nom) \
                .all()
        except:
            return []

    @staticmethod
    def get_cours_by_professeur(user_id):
        """Récupère les cours par professeur"""
        try:
            return CoursModel.query \
                .filter(CoursModel.user_id == user_id) \
                .order_by(CoursModel.nom) \
                .all()
        except:
            return []

    @staticmethod
    def get_cours_with_sessions():
        """Récupère tous les cours avec leurs sessions"""
        try:
            cours = CoursModel.query.all()
            result = []
            for c in cours:
                cours_dict = c.to_dict()
                # Ajouter le nom du professeur
                professeur = UserModel.query.get(c.user_id)
                cours_dict['professeur'] = f"{professeur.prenom} {professeur.nom}" if professeur else "Inconnu"
                result.append(cours_dict)
            return result
        except:
            return []