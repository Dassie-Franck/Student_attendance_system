# app/repositories/student_repository.py
import os
from werkzeug.utils import secure_filename
from app.models.student import EtudiantModel, ProfilModel
from app.database.connDB import db

DATASET_FOLDER = "dataset"


class EtudiantRepository:

    @staticmethod
    def create_etudiant(data, files):
        """
        Crée un nouvel étudiant avec ses photos de profil
        """
        try:
            print("=" * 60)
            print("[REPOSITORY] DÉBUT création étudiant")
            print("=" * 60)

            # DEBUG: Afficher ce qu'on reçoit
            print(f"Données reçues: {data}")
            print(f"Fichiers reçus (clés): {list(files.keys())}")
            for key, file in files.items():
                if file:
                    print(f"  - {key}: {file.filename} ({file.content_type})")
                else:
                    print(f"  - {key}: None")

            # 1️⃣ Créer l'étudiant dans la base de données
            etudiant = EtudiantModel(
                nom=data['nom'],
                prenom=data['prenom'],
                matricule=data['matricule'],
                filiere=data['filiere'],
                annee=data['annee']
            )
            db.session.add(etudiant)
            db.session.flush()  # Important: pour avoir l'ID

            print(f"[✓] Étudiant créé dans DB: ID {etudiant.id}")
            print(f"    Nom: {etudiant.prenom} {etudiant.nom}")
            print(f"    Matricule: {etudiant.matricule}")

            # 2️⃣ Créer le dossier pour les photos
            etudiant_folder = os.path.join(DATASET_FOLDER, f"etudiant_{etudiant.id}")
            os.makedirs(etudiant_folder, exist_ok=True)
            print(f"[✓] Dossier créé: {etudiant_folder}")

            # 3️⃣ Préparer les chemins des fichiers
            photo_paths = {
                'avant': os.path.join(etudiant_folder, "avant.jpg"),
                'gauche': os.path.join(etudiant_folder, "gauche.jpg"),
                'droite': os.path.join(etudiant_folder, "droite.jpg")
            }

            # 4️⃣ Mapping flexible: HTML peut avoir différents noms
            # On essaie plusieurs combinaisons possibles
            file_mapping_attempts = [
                # Tentative 1: Les noms standards
                {'avant': files.get('profil-avant'),
                 'gauche': files.get('profil-gauche'),
                 'droite': files.get('profil-droite')},

                # Tentative 2: Avec 'profil' pour gauche
                {'avant': files.get('profil-avant'),
                 'gauche': files.get('profil'),  # Le HTML a name="profil" pour gauche
                 'droite': files.get('profil-droite')},
            ]

            saved_files = {}

            for attempt in file_mapping_attempts:
                # Vérifier si cet attempt a tous les fichiers
                if all(attempt.values()):
                    print("[✓] Mapping de fichiers trouvé!")
                    for position, file in attempt.items():
                        if file and file.filename:
                            file.save(photo_paths[position])
                            saved_files[position] = photo_paths[position]
                            print(f"    - {position}.jpg sauvegardé")
                    break

            # Vérifier que les 3 fichiers ont été sauvegardés
            if len(saved_files) != 3:
                missing = [p for p in ['avant', 'gauche', 'droite'] if p not in saved_files]
                raise ValueError(f"Fichiers manquants: {missing}")

            # 5️⃣ Créer le profil dans la base de données
            profil = ProfilModel(
                etudiant_id=etudiant.id,
                photo_avant=saved_files['avant'],
                photo_gauche=saved_files['gauche'],
                photo_droite=saved_files['droite']
            )
            db.session.add(profil)

            # 6️⃣ Finaliser la transaction
            db.session.commit()
            print("[✓] Transaction DB commitée avec succès")

            # 7️⃣ Générer les embeddings AUTOMATIQUEMENT
            try:
                from app.services.embedding_service import EmbeddingService
                print("[⚙] Lancement génération des embeddings...")
                EmbeddingService.generate_embeddings_async(etudiant.id)
                print("[✓] Génération embeddings lancée en arrière-plan")
            except ImportError as e:
                print(f"[!] EmbeddingService non disponible: {e}")
                print("[!] Créez app/services/embedding_service.py pour activer cette fonctionnalité")
            except Exception as e:
                print(f"[!] Erreur génération embeddings: {e}")

            print("=" * 60)
            print("[REPOSITORY] FIN création étudiant - SUCCÈS")
            print("=" * 60)

            return etudiant

        except Exception as e:
            print("[✗] ERREUR dans create_etudiant:")
            print(f"    {str(e)}")
            import traceback
            traceback.print_exc()

            # Rollback en cas d'erreur
            try:
                db.session.rollback()
                print("[✓] Rollback effectué")
            except:
                print("[!] Erreur lors du rollback")

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
                # Mettre à jour les photos si fournies
                etudiant_folder = os.path.join(DATASET_FOLDER, f"etudiant_{etudiant.id}")
                os.makedirs(etudiant_folder, exist_ok=True)

                # Sauvegarder les nouvelles photos
                if files.get('profil-avant'):
                    avant_path = os.path.join(etudiant_folder, "avant.jpg")
                    files['profil-avant'].save(avant_path)
                    etudiant.profil.photo_avant = avant_path

                if files.get('profil') or files.get('profil-gauche'):
                    # Gérer les deux noms possibles
                    file = files.get('profil-gauche') or files.get('profil')
                    gauche_path = os.path.join(etudiant_folder, "gauche.jpg")
                    file.save(gauche_path)
                    etudiant.profil.photo_gauche = gauche_path

                if files.get('profil-droite'):
                    droite_path = os.path.join(etudiant_folder, "droite.jpg")
                    files['profil-droite'].save(droite_path)
                    etudiant.profil.photo_droite = droite_path

                # Regénérer les embeddings si photos modifiées
                try:
                    from app.services.embedding_service import EmbeddingService
                    EmbeddingService.generate_embeddings_async(etudiant.id)
                except:
                    pass

            db.session.commit()
            return etudiant
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_etudiant(etudiant):
        try:
            # Supprimer le dossier des photos
            etudiant_folder = os.path.join(DATASET_FOLDER, f"etudiant_{etudiant.id}")
            if os.path.exists(etudiant_folder):
                import shutil
                shutil.rmtree(etudiant_folder)
                print(f"[✓] Dossier supprimé: {etudiant_folder}")

            # Supprimer de la base de données
            db.session.delete(etudiant)
            db.session.commit()
            print(f"[✓] Étudiant {etudiant.id} supprimé de la DB")

        except Exception as e:
            db.session.rollback()
            raise e