# generate_embedding_single.py

import os
import json
import numpy as np
from deepface import DeepFace

def generate_student_embedding(student_folder):
    """
    Génère un embedding moyen pour un étudiant à partir des images dans son dossier
    student_folder: chemin vers dataset/etudiant_id/
    """
    embeddings = []

    # Liste des profils
    profiles = ["avant.jpg"]

    for profile in profiles:
        img_path = os.path.join(student_folder, profile)
        if os.path.exists(img_path):
            # Générer l'embedding pour cette image
            embedding_obj = DeepFace.represent(img_path, model_name="ArcFace", enforce_detection=True)
            embeddings.append(np.array(embedding_obj[0]["embedding"]))
        else:
            print(f"[WARNING] Image {profile} non trouvée dans {student_folder}")

    if not embeddings:
        print(f"[ERROR] Aucune image valide trouvée pour {student_folder}")
        return

    # Calcul de la moyenne des embeddings
    mean_embedding = np.mean(embeddings, axis=0).tolist()

    # Stockage dans embeddings.json dans le même dossier
    output_file = os.path.join(student_folder, "embeddings.json")
    with open(output_file, "w") as f:
        json.dump({"embedding": mean_embedding}, f)

    print(f"[SUCCESS] Embedding généré et sauvegardé dans {output_file}")


if __name__ == "__main__":
    # Remplace par le chemin complet ou relatif vers ton dossier étudiant_14
    student_folder = r"..\dataset\etudiant_15"
    generate_student_embedding(student_folder)
