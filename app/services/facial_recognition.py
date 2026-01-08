import threading
import cv2
import json
import os
import numpy as np
from deepface import DeepFace
from numpy.linalg import norm
import time
from datetime import datetime
from flask import current_app

# =======================
# Configuration
# =======================

# Chemin absolu vers le dataset basé sur ce fichier
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "../../dataset")  # ajuste si nécessaire

MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "yolov8"
THRESHOLD = 0.4  # CORRECTION: Changé de 0.9 à 0.4 (plus restrictif)
FRAME_SKIP = 5

_scan_running = False  # Flag pour start/stop
_current_cap = None  # Variable globale pour la capture vidéo

# =======================
# Variables pour la session de cours
# =======================
_cours_session_id = None  # ID de la session de cours en cours
_detected_students = set()  # Pour éviter les doublons pendant le scan
_stop_requested = False  # Pour arrêter proprement

# Variable pour indiquer si les modèles sont chargés
_models_loaded = False
_db = None
_PresenceModel = None
_CoursSessionModel = None


def _load_models():
    """Charge les modèles SQLAlchemy à la demande."""
    global _models_loaded, _db, _PresenceModel, _CoursSessionModel

    if not _models_loaded:
        try:
            from app import db
            from app.models.attendance import PresenceModel
            from app.models.course_session import CoursSessionModel  # CHANGÉ ICI

            _db = db
            _PresenceModel = PresenceModel
            _CoursSessionModel = CoursSessionModel  # CHANGÉ ICI
            _models_loaded = True
            print("[INFO] Modèles SQLAlchemy chargés")
        except ImportError as e:
            print(f"[WARNING] Impossible de charger les modèles: {e}")
            _models_loaded = False

    return _models_loaded


def cosine_distance(a, b):
    """Distance cosinus entre deux embeddings."""
    return 1 - np.dot(a, b) / (norm(a) * norm(b))


def load_embeddings():
    """Charge tous les embeddings depuis dataset et retourne {student_id: embedding}."""
    embeddings_db = {}

    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dossier dataset introuvable à {DATASET_PATH}")
        return embeddings_db

    print(f"[INFO] Dossiers trouvés dans dataset : {os.listdir(DATASET_PATH)}")

    for student_folder in os.listdir(DATASET_PATH):
        folder_path = os.path.join(DATASET_PATH, student_folder)
        embedding_file = os.path.join(folder_path, "embeddings.json")
        if not os.path.isfile(embedding_file):
            print(f"[WARN] Fichier embeddings.json introuvable dans {student_folder}")
            continue

        with open(embedding_file, "r") as f:
            data = json.load(f)

        # Extraire ID numérique depuis le nom du dossier (ex: etudiant_17 -> 17)
        try:
            student_id = int(student_folder.split("_")[1])
        except:
            print(f"[WARN] Impossible d'extraire l'ID pour {student_folder}")
            continue

        embeddings_db[student_id] = np.array(data["embedding"])
        print(f"[INFO] Embedding chargé pour étudiant {student_id}")

    print(f"[INFO] Total embeddings chargés : {len(embeddings_db)} étudiants")
    return embeddings_db


def _record_presence_internal(etudiant_id, cours_session_id):
    """Logique interne d'enregistrement de présence."""
    try:
        print(f"[DEBUG] Tentative d'enregistrement - Étudiant: {etudiant_id}, Session: {cours_session_id}")

        # Utiliser current_app pour obtenir le contexte actuel
        from flask import current_app

        # Charger les modèles à l'intérieur du contexte
        if not _load_models():
            print("[ERROR] Modèles non chargés")
            return False

        # Vérifier si nous avons un contexte d'application valide
        if not current_app:
            print("[ERROR] Pas de contexte Flask actif")
            return False

        # Vérifier si la session existe
        session = _CoursSessionModel.query.get(cours_session_id)
        if not session:
            print(f"[ERROR] Session {cours_session_id} non trouvée")
            return False

        print(f"[DEBUG] Session trouvée: ID {session.id}")

        # Vérifier si la présence existe déjà
        presence = _PresenceModel.query.filter_by(
            etudiant_id=etudiant_id,
            cours_session_id=cours_session_id
        ).first()

        if presence:
            # Mettre à jour le statut si différent
            if presence.statut != 'P':
                presence.statut = 'P'
                _db.session.commit()
                print(f"[SUCCESS] Présence mise à jour: Étudiant {etudiant_id} -> 'P'")
            else:
                print(f"[INFO] Étudiant {etudiant_id} déjà marqué présent")
        else:
            # Créer une nouvelle présence
            presence = _PresenceModel(
                etudiant_id=etudiant_id,
                cours_session_id=cours_session_id,
                statut='P'  # Présent
            )
            _db.session.add(presence)
            _db.session.commit()
            print(f"[SUCCESS] Nouvelle présence enregistrée: Étudiant {etudiant_id} pour session {cours_session_id}")

            # Vérifier que l'insertion a bien eu lieu
            verify = _PresenceModel.query.filter_by(
                etudiant_id=etudiant_id,
                cours_session_id=cours_session_id
            ).first()
            if verify:
                print(f"[DEBUG] Vérification OK - Présence ID {verify.id} créée")
            else:
                print(f"[ERROR] Vérification échouée - Présence non trouvée après commit")

        return True

    except Exception as e:
        print(f"[ERROR] Erreur base de données lors de l'enregistrement: {str(e)}")
        import traceback
        traceback.print_exc()
        if _db:
            _db.session.rollback()
        return False


def record_presence(etudiant_id, cours_session_id):
    """
    Enregistre la présence d'un étudiant dans la base de données
    en respectant la structure de vos modèles.

    Args:
        etudiant_id: ID de l'étudiant reconnu
        cours_session_id: ID de la session de cours

    Returns:
        bool: True si succès, False sinon
    """
    try:
        print(f"[PRESENCE] Enregistrement - Étudiant: {etudiant_id}, Session: {cours_session_id}")

        # Import des modèles (dans le contexte local pour éviter les problèmes circulaires)
        from app import db
        from app.models.attendance import PresenceModel
        from app.models.course_session import CoursSessionModel  # Votre modèle
        from app.models.student import EtudiantModel  # Votre modèle

        print("[PRESENCE] Modèles importés avec succès")

        # VÉRIFICATION 1: La session existe-t-elle dans cours_session ?
        session = CoursSessionModel.query.get(cours_session_id)
        if not session:
            print(f"[ERROR] Session {cours_session_id} non trouvée dans la table cours_session")

            # Debug: Afficher les sessions disponibles
            sessions_disponibles = CoursSessionModel.query.limit(5).all()
            print(f"[DEBUG] Sessions disponibles (5 premières):")
            for s in sessions_disponibles:
                print(f"  - ID {s.id}: Cours {s.cours_id}, Date {s.date}, Séance {s.seance}")

            return False

        print(f"[PRESENCE] Session trouvée: ID {session.id}, Date: {session.date}, Séance: {session.seance}")

        # VÉRIFICATION 2: L'étudiant existe-t-il ?
        etudiant = EtudiantModel.query.get(etudiant_id)
        if not etudiant:
            print(f"[ERROR] Étudiant {etudiant_id} non trouvé")
            return False

        print(f"[PRESENCE] Étudiant trouvé: {etudiant.prenom} {etudiant.nom} (ID: {etudiant.id})")

        # VÉRIFICATION 3: La présence existe-t-elle déjà ?
        presence_existante = PresenceModel.query.filter_by(
            etudiant_id=etudiant_id,
            cours_session_id=cours_session_id
        ).first()

        if presence_existante:
            # Mettre à jour si nécessaire
            if presence_existante.statut != 'P':
                presence_existante.statut = 'P'
                db.session.commit()
                print(f"[SUCCESS] Présence mise à jour: {etudiant.prenom} {etudiant.nom} -> 'P'")
            else:
                print(f"[INFO] {etudiant.prenom} {etudiant.nom} déjà présent")
            return True
        else:
            # Créer une nouvelle présence
            nouvelle_presence = PresenceModel(
                etudiant_id=etudiant_id,
                cours_session_id=cours_session_id,
                statut='P'  # P = présent
            )

            db.session.add(nouvelle_presence)
            db.session.commit()

            # Vérifier que l'insertion a réussi
            presence_verifiee = PresenceModel.query.filter_by(
                etudiant_id=etudiant_id,
                cours_session_id=cours_session_id
            ).first()

            if presence_verifiee:
                print(f"PRÉSENCE ENREGISTRÉE:")
                print(f"   - Étudiant: {etudiant.prenom} {etudiant.nom}")
                print(f"   - Session: {session.id} (Date: {session.date}, Séance: {session.seance})")
                print(f"   - Cours: {session.cours.nom if session.cours else 'N/A'}")
                print(f"   - Statut: {presence_verifiee.statut}")
                print(f"   - Heure: {presence_verifiee.date_enregistrement}")
                return True
            else:
                print(f"[ERROR] Présence créée mais non retrouvée")
                return False

    except Exception as e:
        print(f"[ERROR] Erreur lors de l'enregistrement: {str(e)}")
        import traceback
        traceback.print_exc()

        # Rollback en cas d'erreur
        try:
            db.session.rollback()
        except:
            pass

        return False


def safe_release_camera():
    """Libère la caméra de manière sécurisée."""
    global _current_cap

    if _current_cap is not None:
        try:
            _current_cap.release()
            print("[INFO] Webcam libérée")
        except Exception as e:
            print(f"[WARNING] Erreur lors de la libération de la webcam: {e}")
        finally:
            _current_cap = None

    # Fermer toutes les fenêtres OpenCV
    try:
        cv2.destroyAllWindows()
        # Donner un peu de temps à OpenCV
        cv2.waitKey(1)
    except:
        pass


def safe_open_camera():
    """Ouvre la caméra de manière sécurisée."""
    global _current_cap

    # D'abord fermer toute caméra existante
    safe_release_camera()

    # Attendre un peu pour laisser le système se stabiliser
    time.sleep(0.5)

    # Essayer différents index de caméra
    camera_indexes = [0, 1, 2]

    for index in camera_indexes:
        try:
            # Essayer avec CAP_DSHOW sur Windows pour de meilleures performances
            if os.name == 'nt':  # Windows
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            else:  # Linux/Mac
                cap = cv2.VideoCapture(index)

            if cap.isOpened():
                # Tester si on peut lire une frame
                ret, test_frame = cap.read()
                if ret:
                    print(f"[INFO] Webcam trouvée à l'index {index}")

                    # Configurer les propriétés pour de meilleures performances
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)

                    _current_cap = cap
                    return cap
                else:
                    cap.release()
            else:
                if cap is not None:
                    cap.release()

        except Exception as e:
            print(f"[WARNING] Erreur avec la webcam index {index}: {e}")
            continue

    print("Aucune webcam accessible")
    return None


# =======================
# Scan Webcam avec enregistrement des présences - VERSION AMÉLIORÉE
# =======================

def run_face_scan(cours_session_id):
    """
    Lance le scan facial via la webcam et enregistre les présences.
    """
    global _scan_running, _cours_session_id, _detected_students, _stop_requested

    print(f"[DEBUG] ======================================")
    print(f"[DEBUG] DÉBUT run_face_scan - VERSION AMÉLIORÉE")
    print(f"[DEBUG] cours_session_id = {cours_session_id}")
    print(f"[DEBUG] ======================================")

    if not cours_session_id:
        print("[ERROR] Aucun cours_session_id fourni")
        return []

    _cours_session_id = cours_session_id
    _detected_students.clear()
    _scan_running = True
    _stop_requested = False

    print(f"[INFO] Démarrage du scan pour la session: {_cours_session_id}")

    # Ouvrir la caméra de manière sécurisée
    cap = safe_open_camera()
    if cap is None:
        print(" Impossible d'ouvrir la webcam")
        return []

    embeddings_db = load_embeddings()
    if len(embeddings_db) == 0:
        print(" Aucun embedding trouvé, impossible de scanner")
        safe_release_camera()
        return []

    frame_count = 0
    faces_info = []
    prev_time = time.time()

    # Variables pour l'animation du cadre
    pulse_factor = 0
    pulse_direction = 1

    # Statistiques
    total_detections = 0
    unique_detections = 0

    print("[INFO] Appuyez sur 'q' pour quitter...")

    try:
        while _scan_running and not _stop_requested:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Impossible de lire la frame, tentative de récupération...")
                # Tentative de récupération
                time.sleep(0.1)
                continue

            frame_count += 1

            if frame_count % FRAME_SKIP == 0:
                faces_info = []
                try:
                    # Extraction des visages AVEC les landmarks
                    results = DeepFace.extract_faces(
                        frame,
                        detector_backend=DETECTOR_BACKEND,
                        enforce_detection=False,
                        align=True  # Important pour obtenir les landmarks
                    )
                except Exception as e:
                    print(f"[WARNING] Erreur extraction visages: {e}")
                    continue

                for face in results:
                    area = face["facial_area"]
                    x, y, w, h = area["x"], area["y"], area["w"], area["h"]

                    # Vérifier que la zone du visage est valide
                    if w <= 0 or h <= 0 or x < 0 or y < 0:
                        continue

                    # S'assurer que les coordonnées sont dans l'image
                    h_img, w_img = frame.shape[:2]
                    x1, y1 = max(0, x), max(0, y)
                    x2, y2 = min(w_img, x + w), min(h_img, y + h)

                    if x2 <= x1 or y2 <= y1:
                        continue

                    face_crop = frame[y1:y2, x1:x2]

                    if face_crop.size == 0:
                        continue

                    try:
                        # Obtenir l'embedding
                        emb = DeepFace.represent(
                            face_crop,
                            model_name=MODEL_NAME,
                            enforce_detection=False,
                            detector_backend=DETECTOR_BACKEND  # CORRECTION: Ajouté
                        )[0]["embedding"]

                        # Essayer d'obtenir les landmarks
                        landmarks = []
                        try:
                            # DeepFace.detectFace retourne aussi des landmarks
                            face_analysis = DeepFace.analyze(
                                face_crop,
                                actions=['landmarks'],
                                detector_backend=DETECTOR_BACKEND,
                                enforce_detection=False,
                                silent=True
                            )
                            if isinstance(face_analysis, list) and len(face_analysis) > 0:
                                if 'region' in face_analysis[0]:
                                    landmarks_data = face_analysis[0].get('region', {})
                                    # Extraire les points clés si disponibles
                                    if 'left_eye' in landmarks_data and 'right_eye' in landmarks_data:
                                        landmarks.append((
                                            int(landmarks_data['left_eye']['x']),
                                            int(landmarks_data['left_eye']['y'])
                                        ))
                                        landmarks.append((
                                            int(landmarks_data['right_eye']['x']),
                                            int(landmarks_data['right_eye']['y'])
                                        ))
                        except:
                            landmarks = []

                    except Exception as e:
                        print(f"[WARNING] Erreur représentation: {e}")
                        continue

                    # Reconnaissance
                    min_dist = float("inf")
                    match_id = None

                    for student_id, stored_emb in embeddings_db.items():
                        dist = cosine_distance(emb, stored_emb)
                        if dist < min_dist:
                            min_dist = dist
                            if dist < THRESHOLD:  # CORRECTION: Utilise le seuil corrigé
                                match_id = student_id
                                print(f"[DEBUG] Match trouvé: ID {student_id} avec distance {dist:.3f}")
                                break  # On prend le premier match

                    # CORRECTION: Ajouter une vérification supplémentaire
                    # Pour éviter les faux positifs, vérifier la distance absolue
                    if match_id is not None and min_dist < THRESHOLD:
                        total_detections += 1

                        print(f"[DEBUG] === Traitement étudiant {match_id} ===")

                        # Éviter les doublons fréquents
                        if match_id not in _detected_students:
                            # Enregistrer dans la base de données
                            print(f"[DEBUG] Appel record_presence pour étudiant {match_id}")
                            if record_presence(match_id, _cours_session_id):
                                _detected_students.add(match_id)
                                unique_detections += 1
                                print(f" Étudiant {match_id} reconnu et enregistré (distance: {min_dist:.3f})")
                            else:
                                print(f" Échec enregistrement pour étudiant {match_id}")
                        else:
                            print(f"[INFO] Étudiant {match_id} déjà détecté dans cette session")

                        # Stocker les informations avec les landmarks
                        faces_info.append((x, y, w, h, match_id, min_dist, True, landmarks))
                    else:
                        # Visage non reconnu
                        faces_info.append((x, y, w, h, None, min_dist, False, landmarks))

            # --- Animation du cadre (pulsation)
            pulse_factor += pulse_direction * 0.05
            if pulse_factor > 1.0:
                pulse_factor = 1.0
                pulse_direction = -1
            elif pulse_factor < 0.0:
                pulse_factor = 0.0
                pulse_direction = 1

            # --- Affichage AVEC AMÉLIORATIONS
            for x, y, w, h, student_id, dist, is_recognized, landmarks in faces_info:

                # 1. DÉTERMINER LA COULEUR (ROUGE → VERT)
                if student_id is not None and is_recognized:
                    # ÉTUDIANT RECONNU - dégradé vert
                    base_color = (0, 255, 0)  # Vert
                    # Effet de "pulsation" vert
                    pulse_intensity = int(50 * pulse_factor)
                    color = (
                        min(255, base_color[0] + pulse_intensity),
                        min(255, base_color[1] - pulse_intensity),
                        base_color[2]
                    )
                    status_text = f"✓ ID: {student_id} ({dist:.2f})"
                    is_recognized_now = True
                else:
                    # VISAGE NON RECONNU - rouge pulsant
                    base_color = (0, 0, 255)  # Rouge
                    pulse_intensity = int(30 * pulse_factor)
                    color = (
                        base_color[0],
                        base_color[1],
                        min(255, base_color[2] + pulse_intensity)
                    )
                    status_text = "Inconnu"
                    is_recognized_now = False

                # 2. CADRE QUI SUIT LE VISAGE (avec effet)
                # Cadre extérieur épais
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

                # Cadre intérieur plus fin (effet de profondeur)
                inner_margin = 5
                cv2.rectangle(frame,
                              (x + inner_margin, y + inner_margin),
                              (x + w - inner_margin, y + h - inner_margin),
                              color, 1)

                # Coins décoratifs
                corner_length = 15
                # Coin supérieur gauche
                cv2.line(frame, (x, y), (x + corner_length, y), color, 2)
                cv2.line(frame, (x, y), (x, y + corner_length), color, 2)
                # Coin supérieur droit
                cv2.line(frame, (x + w, y), (x + w - corner_length, y), color, 2)
                cv2.line(frame, (x + w, y), (x + w, y + corner_length), color, 2)
                # Coin inférieur gauche
                cv2.line(frame, (x, y + h), (x + corner_length, y + h), color, 2)
                cv2.line(frame, (x, y + h), (x, y + h - corner_length), color, 2)
                # Coin inférieur droit
                cv2.line(frame, (x + w, y + h), (x + w - corner_length, y + h), color, 2)
                cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_length), color, 2)

                # 3. POINTS SUR LES REPÈRES FACIAUX
                if landmarks and len(landmarks) >= 2:
                    # Ajuster les coordonnées des landmarks à la frame originale
                    for landmark_x, landmark_y in landmarks:
                        # Convertir les coordonnées relatives en absolues
                        abs_x = x + landmark_x
                        abs_y = y + landmark_y

                        # Dessiner les points des yeux
                        cv2.circle(frame, (abs_x, abs_y), 4, (0, 255, 255), -1)  # Centre jaune
                        cv2.circle(frame, (abs_x, abs_y), 6, color, 1)  # Bordure de couleur

                        # Petits points intérieurs pour plus de détails
                        cv2.circle(frame, (abs_x, abs_y), 2, (255, 255, 255), -1)

                    # Si on a les deux yeux, dessiner une ligne entre eux
                    if len(landmarks) >= 4:
                        eye1 = (x + landmarks[0][0], y + landmarks[0][1])
                        eye2 = (x + landmarks[1][0], y + landmarks[1][1])
                        cv2.line(frame, eye1, eye2, (255, 255, 0), 1, cv2.LINE_AA)

                # Ajouter des points fictifs pour d'autres parties du visage
                # si les landmarks ne sont pas disponibles
                if not landmarks:
                    # Points approximatifs pour les yeux
                    eye_y = y + h // 3
                    left_eye_x = x + w // 4
                    right_eye_x = x + 3 * w // 4

                    cv2.circle(frame, (left_eye_x, eye_y), 3, (0, 255, 255), -1)
                    cv2.circle(frame, (right_eye_x, eye_y), 3, (0, 255, 255), -1)

                    # Point pour le nez
                    nose_x = x + w // 2
                    nose_y = y + h // 2
                    cv2.circle(frame, (nose_x, nose_y), 3, (255, 0, 0), -1)

                    # Points pour la bouche
                    mouth_y = y + 2 * h // 3
                    mouth_left = x + w // 3
                    mouth_right = x + 2 * w // 3
                    cv2.circle(frame, (mouth_left, mouth_y), 2, (255, 0, 255), -1)
                    cv2.circle(frame, (mouth_right, mouth_y), 2, (255, 0, 255), -1)

                # 4. TEXTE AVEC FOND POUR MEILLEURE LISIBILITÉ
                text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                text_x = x
                text_y = y - 10 if y > 30 else y + h + 20

                # Fond semi-transparent pour le texte
                overlay = frame.copy()
                cv2.rectangle(overlay,
                              (text_x - 5, text_y - text_size[1] - 5),
                              (text_x + text_size[0] + 5, text_y + 5),
                              (0, 0, 0), -1)

                # Fusionner avec transparence
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

                # Texte
                cv2.putText(frame, status_text, (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # 5. INDICATEUR VISUEL SUPPLEMENTAIRE
                if is_recognized_now:
                    # Checkmark vert
                    cv2.putText(frame, "✓", (x + w - 25, y + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

                    # Animation de confirmation (cercle pulsant)
                    pulse_radius = int(10 + 5 * pulse_factor)
                    cv2.circle(frame, (x + w - 15, y + 15), pulse_radius, (0, 255, 0), 2)

            # --- INFORMATIONS STATISTIQUES AVEC STYLE
            info_bg_height = 110
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, info_bg_height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

            info_texts = [
                f"SESSION: {_cours_session_id}",
                f"DÉTECTIONS: {unique_detections}/{len(embeddings_db)}",
                f"TOTAL SCANS: {total_detections}",
                f"STATUT: {'ACTIF' if _scan_running else 'ARRÊTÉ'}",
                "APPUYEZ SUR 'Q' POUR QUITTER"
            ]

            y_offset = 25
            for i, text in enumerate(info_texts):
                color = (0, 255, 0) if i == 0 else (255, 255, 255)
                font_size = 0.6 if i > 0 else 0.7
                cv2.putText(frame, text, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size, color, 2 if i == 0 else 1)
                y_offset += 22

            # --- FPS avec style
            curr_time = time.time()
            fps = int(1 / (curr_time - prev_time))
            prev_time = curr_time

            fps_color = (0, 255, 0) if fps > 15 else (0, 165, 255) if fps > 10 else (0, 0, 255)
            fps_text = f"FPS: {fps}"
            fps_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]

            # Fond FPS
            fps_bg = (frame.shape[1] - fps_size[0] - 20, 10, fps_size[0] + 10, fps_size[1] + 10)
            cv2.rectangle(frame,
                          (fps_bg[0] - 5, fps_bg[1] - 5),
                          (fps_bg[0] + fps_bg[2] + 5, fps_bg[1] + fps_bg[3] + 5),
                          (0, 0, 0), -1)

            cv2.putText(frame, fps_text, (frame.shape[1] - fps_size[0] - 15, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, fps_color, 2)

            # --- LÉGENDE DES COULEURS
            legend_texts = [
                "ROUGE: Visage détecté",
                "VERT: Étudiant reconnu",
                "JAUNE: Points de reconnaissance"
            ]

            legend_y = frame.shape[0] - 10
            for text in reversed(legend_texts):
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.putText(frame, text, (10, legend_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                legend_y -= 20

            # Affichage de la fenêtre
            cv2.imshow("🎥 Reconnaissance Faciale - Scan des Présences 🎓", frame)

            # Gestion des touches
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[INFO] Arrêt demandé par l'utilisateur")
                _stop_requested = True
                break
            elif key == ord("s"):
                # Arrêt manuel
                print("[INFO] Arrêt manuel")
                _stop_requested = True
                break
            elif key == ord(" "):  # Espace pour pause
                print("[INFO] Mise en pause - Appuyez sur une touche pour continuer")
                cv2.waitKey(0)

    except Exception as e:
        print(f"[ERROR] Erreur pendant le scan: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Nettoyage garanti
        safe_release_camera()

    # Résumé du scan
    print("\n" + "=" * 60)
    print(" RÉSUMÉ DU SCAN - SESSION TERMINÉE")
    print("=" * 60)
    print(f" Session de cours: {_cours_session_id}")
    print(f" Étudiants détectés: {unique_detections}")
    print(f" Total des scans: {total_detections}")
    print(f" Étudiants enregistrés: {len(_detected_students)}")

    if _detected_students:
        print(" IDs des étudiants détectés:", sorted(list(_detected_students)))
    else:
        print("  Aucun étudiant détecté")

    print("=" * 60)
    print("[INFO] Scan terminé avec succès ✓")

    _scan_running = False
    return list(_detected_students)


def stop_scan():
    """Arrête le scan proprement."""
    global _scan_running, _stop_requested
    _stop_requested = True
    _scan_running = False

    # Forcer la libération de la caméra
    safe_release_camera()

    print("[INFO] Demande d'arrêt du scan...")


# =======================
# Fonction wrapper pour les threads
# =======================
def run_face_scan_with_context(cours_session_id):
    """
    Wrapper pour exécuter le scan avec un contexte Flask.
    À utiliser dans les threads.
    """
    print(f"[DEBUG] ======================================")
    print(f"[DEBUG] DÉBUT run_face_scan_with_context")
    print(f"[DEBUG] Thread: {threading.current_thread().name}")
    print(f"[DEBUG] cours_session_id: {cours_session_id}")
    print(f"[DEBUG] ======================================")

    try:
        from app import create_app

        # Créer l'application Flask
        app = create_app()

        print(f"[DEBUG] Application Flask créée")

        # Utiliser le contexte d'application
        with app.app_context():
            print(f"[DEBUG] Contexte d'application activé")

            # Forcer le chargement des modèles dans ce contexte
            _load_models()

            print(f"[DEBUG] Modèles chargés: {_models_loaded}")

            # Exécuter le scan dans le contexte
            result = run_face_scan(cours_session_id)

            print(f"[DEBUG] Scan terminé, résultat: {result}")
            return result

    except Exception as e:
        print(f"[ERROR] Erreur critique dans run_face_scan_with_context: {str(e)}")
        import traceback
        traceback.print_exc()
        safe_release_camera()  # Nettoyage en cas d'erreur
        return []