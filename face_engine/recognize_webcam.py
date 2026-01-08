import cv2
import json
import os
import numpy as np
from deepface import DeepFace
from numpy.linalg import norm
import time

DATASET_PATH = "../dataset"
MODEL_NAME = "ArcFace"  # ou "Facenet512"
DETECTOR_BACKEND = "yolov8"
THRESHOLD = 0.45
FRAME_SKIP = 5  # nombre de frames avant recalcul embedding

# --- Distance cosinus ---
def cosine_distance(a, b):
    return 1 - np.dot(a, b) / (norm(a) * norm(b))

# --- Chargement embeddings ---
def load_embeddings():
    embeddings_db = {}
    for student_id in os.listdir(DATASET_PATH):
        student_folder = os.path.join(DATASET_PATH, student_id)
        embedding_file = os.path.join(student_folder, "embeddings.json")
        if not os.path.isfile(embedding_file):
            continue
        with open(embedding_file, "r") as f:
            data = json.load(f)
        embeddings_db[student_id] = np.array(data["embedding"])
    return embeddings_db

# --- Webcam ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print(" Webcam non accessible")
    exit()

embeddings_db = load_embeddings()
print(f"[INFO] {len(embeddings_db)} étudiants chargés")

frame_count = 0
faces_info = []  # liste (bbox, name, distance)
prev_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    # --- Détection et embedding toutes les FRAME_SKIP frames ---
    if frame_count % FRAME_SKIP == 0:
        faces_info = []
        results = DeepFace.extract_faces(frame, detector_backend=DETECTOR_BACKEND, enforce_detection=False)
        for face in results:
            x, y, w, h = face["facial_area"]["x"], face["facial_area"]["y"], face["facial_area"]["w"], face["facial_area"]["h"]
            face_crop = frame[y:y+h, x:x+w]

            try:
                emb = DeepFace.represent(face_crop, model_name=MODEL_NAME, enforce_detection=False)[0]["embedding"]
            except:
                continue

            # Reconnaissance
            min_dist = float("inf")
            match_name = "INCONNU"
            for student_id, stored_emb in embeddings_db.items():
                dist = cosine_distance(emb, stored_emb)
                if dist < min_dist:
                    min_dist = dist
                    if dist < THRESHOLD:
                        match_name = student_id

            faces_info.append((x, y, w, h, match_name, min_dist))

    # --- Affichage ---
    for x, y, w, h, name, dist in faces_info:
        color = (0, 255, 0) if name != "INCONNU" else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        text = f"{name} ({dist:.2f})" if name != "INCONNU" else "Visage inconnu"
        cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # --- Calcul FPS ---
    curr_time = time.time()
    fps = 1.0 / (curr_time - prev_time)
    prev_time = curr_time
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Reconnaissance Faciale - ArcFace + YOLO", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()