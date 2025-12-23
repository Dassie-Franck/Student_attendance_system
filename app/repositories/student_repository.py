import os
from app.models.student import EtudiantModel, ProfilModel
from app.database.connDB import db
from werkzeug.utils import secure_filename

DATASET_FOLDER = "dataset"  # dossier principal pour stocker les images

class EtudiantRepository:

    @staticmethod
    def create_etudiant(data, files):
        """
        data: dict {nom, prenom, matricule, filiere, annee}
        files: dict {avant, gauche, droite} provenant du formulaire Flask
        """
        try:
            # Créer l'étudiant
            etudiant = EtudiantModel(
                nom=data['nom'],
                prenom=data['prenom'],
                matricule=data['matricule'],
                filiere=data['filiere'],
                annee=data['annee']
            )
            db.session.add(etudiant)
            db.session.flush()  # flush pour récupérer l'ID avant commit

            # Créer le dossier pour les images
            etudiant_folder = os.path.join(DATASET_FOLDER, f"etudiant_{etudiant.id}")
            os.makedirs(etudiant_folder, exist_ok=True)

            # Sauvegarder les fichiers uploadés
            photo_avant_path = os.path.join(etudiant_folder, "avant.jpg")
            photo_gauche_path = os.path.join(etudiant_folder, "gauche.jpg")
            photo_droite_path = os.path.join(etudiant_folder, "droite.jpg")

            files['avant'].save(photo_avant_path)
            files['gauche'].save(photo_gauche_path)
            files['droite'].save(photo_droite_path)

            # Créer le profil
            profil = ProfilModel(
                etudiant_id=etudiant.id,
                photo_avant=photo_avant_path,
                photo_gauche=photo_gauche_path,
                photo_droite=photo_droite_path
            )
            db.session.add(profil)

            # Commit transaction
            db.session.commit()
            return etudiant

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_all():
        return EtudiantModel.query.all()

    @staticmethod
    def get_by_id(etudiant_id):
        return EtudiantModel.query.get(etudiant_id)

    @staticmethod
    def update_etudiant(etudiant, data, files=None):
        try:
            etudiant.nom = data['nom']
            etudiant.prenom = data['prenom']
            etudiant.matricule = data['matricule']
            etudiant.filiere = data['filiere']
            etudiant.annee = data['annee']

            if files:
                # Mettre à jour les images si elles existent
                etudiant_folder = os.path.join(DATASET_FOLDER, f"etudiant_{etudiant.id}")
                os.makedirs(etudiant_folder, exist_ok=True)

                if files.get('avant'):
                    avant_path = os.path.join(etudiant_folder, "avant.jpg")
                    files['avant'].save(avant_path)
                    etudiant.profil.photo_avant = avant_path
                if files.get('gauche'):
                    gauche_path = os.path.join(etudiant_folder, "gauche.jpg")
                    files['gauche'].save(gauche_path)
                    etudiant.profil.photo_gauche = gauche_path
                if files.get('droite'):
                    droite_path = os.path.join(etudiant_folder, "droite.jpg")
                    files['droite'].save(droite_path)
                    etudiant.profil.photo_droite = droite_path

            db.session.commit()
            return etudiant
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_etudiant(etudiant):
        try:
            # Supprimer le dossier des images
            etudiant_folder = os.path.join(DATASET_FOLDER, f"etudiant_{etudiant.id}")
            if os.path.exists(etudiant_folder):
                import shutil
                shutil.rmtree(etudiant_folder)
            # Supprimer de la DB
            db.session.delete(etudiant)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
