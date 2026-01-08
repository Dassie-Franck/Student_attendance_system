# app/services/embedding_service.py
import os
import json
import numpy as np
from deepface import DeepFace
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:

    @staticmethod
    def generate_embeddings_for_student(student_id):
        """
        Génère automatiquement les embeddings pour un étudiant
        """
        try:
            print(f"[EMBEDDING] Début génération pour étudiant {student_id}")

            dataset_folder = "dataset"
            student_folder = os.path.join(dataset_folder, f"etudiant_{student_id}")

            if not os.path.exists(student_folder):
                print(f"[✗] Dossier non trouvé: {student_folder}")
                return False

            # Vérifier que les 3 photos existent
            required_files = ["avant.jpg", "gauche.jpg", "droite.jpg"]
            missing_files = []

            for filename in required_files:
                filepath = os.path.join(student_folder, filename)
                if not os.path.exists(filepath):
                    missing_files.append(filename)

            if missing_files:
                print(f"[✗] Fichiers manquants: {missing_files}")
                return False

            print(f"[✓] Tous les fichiers présents pour étudiant {student_id}")

            # Générer les embeddings pour chaque photo
            embeddings = []

            for filename in required_files:
                img_path = os.path.join(student_folder, filename)

                try:
                    print(f"  - Traitement {filename}...")
                    embedding_obj = DeepFace.represent(
                        img_path=img_path,
                        model_name="ArcFace",
                        enforce_detection=True,
                        detector_backend="yolov8"
                    )

                    embedding_vector = np.array(embedding_obj[0]["embedding"])
                    embeddings.append(embedding_vector)
                    print(f"  [✓] {filename} traité")

                except Exception as e:
                    print(f"  [✗] Erreur {filename}: {e}")
                    continue

            if not embeddings:
                print("[✗] Aucun embedding généré")
                return False

            # Calculer la moyenne
            print(f"[⚙] Calcul moyenne sur {len(embeddings)} embeddings...")
            mean_embedding = np.mean(embeddings, axis=0).tolist()

            # Sauvegarder
            output_file = os.path.join(student_folder, "embeddings.json")

            embedding_data = {
                "student_id": student_id,
                "embedding": mean_embedding,
                "generated_at": datetime.now().isoformat(),
                "model": "ArcFace",
                "image_count": len(embeddings),
                "images_used": required_files
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(embedding_data, f, ensure_ascii=False, indent=2)

            print(f"[✓] Embedding sauvegardé: {output_file}")
            print(f"[✓] Taille embedding: {len(mean_embedding)} dimensions")

            return True

        except Exception as e:
            print(f"[✗] Erreur génération embeddings: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def generate_embeddings_async(student_id):
        """
        Lance en arrière-plan
        """

        def generate_in_thread():
            try:
                EmbeddingService.generate_embeddings_for_student(student_id)
            except Exception as e:
                logger.error(f"Erreur thread embeddings: {e}")

        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

        print(f"[⚙] Génération embeddings démarrée pour étudiant {student_id}")
        return thread