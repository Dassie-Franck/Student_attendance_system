from app.repositories.course_repository import CoursRepository


class CoursService:

    @staticmethod
    def create_course(user_id, nom, filiere, semestre, sessions):
        return CoursRepository.create_cours(
            user_id, nom, filiere, semestre, sessions
        )

    @staticmethod
    def get_course(cours_id):
        return CoursRepository.get_by_id(cours_id)

    @staticmethod
    def get_all_courses():
        return CoursRepository.get_all()

    @staticmethod
    def update_course(cours, nom, filiere, semestre, sessions):
        return CoursRepository.update(
            cours, nom, filiere, semestre, sessions
        )

    @staticmethod
    def delete_course(cours):
        CoursRepository.delete(cours)
