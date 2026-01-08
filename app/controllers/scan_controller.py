# app/controllers/scan_controller.py
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
import threading
import logging
from app.services.facial_recognition import run_face_scan_with_context, stop_scan

scan_bp = Blueprint("scan", __name__)
scan_thread = None

# Configuration du logger
logger = logging.getLogger(__name__)


@scan_bp.route("/start", methods=["POST"])
def start_scan():
    try:
        # Debug: Afficher TOUTES les informations de la requête
        logger.info(f"\n{'=' * 60}")
        logger.info("=== NOUVELLE REQUÊTE SCAN START ===")
        logger.info(f"URL: {request.url}")
        logger.info(f"Méthode: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Données brutes: {request.get_data(as_text=True)}")

        # Vérifier le Content-Type
        if not request.is_json:
            content_type = request.content_type or 'non spécifié'
            logger.error(f"Content-Type incorrect: {content_type}. Attendu: application/json")
            return jsonify({
                "error": "Content-Type doit être application/json",
                "received_content_type": content_type
            }), 400

        # Essayer de lire le JSON
        data = request.get_json(silent=True, force=False)
        logger.info(f"Données JSON parsées: {data}")
        logger.info(f"Type de données: {type(data)}")

        # Vérifier si le JSON est valide
        if data is None:
            logger.error("JSON invalide, vide ou Content-Type incorrect")
            logger.error(f"Raw data: {request.get_data(as_text=True)[:200]}")
            return jsonify({
                "error": "JSON invalide ou vide. Vérifiez le format et Content-Type",
                "hint": "Assurez-vous d'envoyer Content-Type: application/json"
            }), 400

        # Vérifier si c'est un dictionnaire
        if not isinstance(data, dict):
            logger.error(f"Données JSON doivent être un objet, reçu: {type(data)}")
            return jsonify({
                "error": "Les données doivent être un objet JSON",
                "received_type": str(type(data))
            }), 400

        # Vérifier la présence de cours_session_id
        if "cours_session_id" not in data:
            # Vérifier d'autres noms possibles (au cas où)
            possible_keys = ["cours_session_id", "session_id", "sessionId", "coursSessionId"]
            found_keys = [k for k in possible_keys if k in data]

            if found_keys:
                logger.warning(f"Clé alternative trouvée: {found_keys}")
                # Utiliser la première clé alternative trouvée
                cours_session_id = data[found_keys[0]]
            else:
                logger.error(f"cours_session_id manquant. Clés disponibles: {list(data.keys())}")
                return jsonify({
                    "error": "cours_session_id manquant",
                    "available_keys": list(data.keys()),
                    "expected_keys": ["cours_session_id"]
                }), 400
        else:
            cours_session_id = data["cours_session_id"]

        logger.info(f"cours_session_id récupéré: {cours_session_id} (type: {type(cours_session_id)})")

        # Validation
        if cours_session_id is None:
            return jsonify({"error": "cours_session_id ne peut pas être null"}), 400

        if isinstance(cours_session_id, str) and cours_session_id.strip() == "":
            return jsonify({"error": "cours_session_id ne peut pas être une chaîne vide"}), 400

        try:
            cours_session_id = int(cours_session_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur conversion cours_session_id en int: {e}")
            return jsonify({
                "error": "cours_session_id doit être un nombre valide",
                "received_value": str(cours_session_id),
                "received_type": str(type(cours_session_id))
            }), 400

        # Vérifier que l'ID est positif
        if cours_session_id <= 0:
            return jsonify({"error": "cours_session_id doit être un nombre positif"}), 400

        global scan_thread

        # Vérifier si un scan est déjà en cours
        if scan_thread and scan_thread.is_alive():
            logger.warning("Tentative de démarrage alors qu'un scan est déjà en cours")
            return jsonify({"error": "Un scan est déjà en cours"}), 400

        # Démarrer le scan dans un thread séparé avec contexte
        scan_thread = threading.Thread(
            target=run_face_scan_with_context,
            args=(cours_session_id,),
            daemon=True
        )
        scan_thread.start()

        logger.info(f" Scan démarré pour la session {cours_session_id}")
        logger.info("=== FIN START SCAN ===")
        logger.info(f"{'=' * 60}\n")

        return jsonify({
            "success": True,
            "message": "Scan démarré avec succès",
            "cours_session_id": cours_session_id,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f" Erreur inattendue dans start_scan: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erreur interne du serveur",
            "details": str(e) if current_app.config.get('DEBUG') else "Contactez l'administrateur"
        }), 500


# ... reste du code inchangé ...

@scan_bp.route("/stop", methods=["POST"])
def stop_scan_route():
    try:
        stop_scan()
        logger.info("Scan arrêté")
        return jsonify({"message": "Scan arrêté"}), 200
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt: {str(e)}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@scan_bp.route("/status", methods=["GET"])
def scan_status():
    try:
        from app.services.facial_recognition import _scan_running, _detected_students
        return jsonify({
            "running": _scan_running,
            "detected_count": len(_detected_students),
            "detected_students": list(_detected_students)
        }), 200
    except Exception as e:
        logger.error(f"Erreur statut: {str(e)}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


# Route de test
@scan_bp.route("/test", methods=["GET"])
def test():
    return jsonify({
        "message": "Scan API fonctionne",
        "endpoints": {
            "/start": "POST - Démarrer scan",
            "/stop": "POST - Arrêter scan",
            "/status": "GET - Statut scan"
        }
    }), 200