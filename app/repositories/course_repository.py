from app.models.course import CoursModel, CoursSessionModel
from app.database.connDB import db
from sqlalchemy.exc import SQLAlchemyError


class CoursRepository:

    @staticmethod
    def create_cours(user_id, nom, filiere, semestre, sessions):
        try:
            cours = CoursModel(
                nom=nom,
                user_id=user_id,
                filiere=filiere,
                semestre=semestre
            )

            for s in sessions:
                cours.sessions.append(
                    CoursSessionModel(
                        date=s["date"],
                        seance=s["seance"]
                    )
                )

            db.session.add(cours)
            db.session.commit()
            return cours

        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id(cours_id):
        return CoursModel.query.get(cours_id)

    @staticmethod
    def get_all():
        return CoursModel.query.all()

    @staticmethod
    def update(cours, nom, filiere, semestre, sessions):
        try:
            cours.nom = nom
            cours.filiere = filiere
            cours.semestre = semestre

            # reset sessions (cascade)
            cours.sessions.clear()

            for s in sessions:
                cours.sessions.append(
                    CoursSessionModel(
                        date=s["date"],
                        seance=s["seance"]
                    )
                )

            db.session.commit()
            return cours

        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def delete(cours):
        try:
            db.session.delete(cours)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
