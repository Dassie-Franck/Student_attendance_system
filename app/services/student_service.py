# app/services/student_service.py
from app.repositories.student_repository import EtudiantRepository

class EtudiantService:

    @staticmethod
    def create(data, files):
        # CORRECTION: utilisez create_etudiant, pas create
        return EtudiantRepository.create_etudiant(data, files)

    @staticmethod
    def get_all():
        return EtudiantRepository.get_all()

    @staticmethod
    def get_by_id(etudiant_id):
        return EtudiantRepository.get_by_id(etudiant_id)

    @staticmethod
    def update(etudiant, data, files=None):
        return EtudiantRepository.update_etudiant(etudiant, data, files)

    @staticmethod
    def delete(etudiant):
        return EtudiantRepository.delete_etudiant(etudiant)