from app.database.connDB import db
from app.models.course_session import CoursSessionModel

class CoursSessionRepository:

    @staticmethod
    def create(cours_id, date, seance):
        session = CoursSessionModel(
            cours_id=cours_id,
            date=date,
            seance=seance
        )
        db.session.add(session)
        return session
