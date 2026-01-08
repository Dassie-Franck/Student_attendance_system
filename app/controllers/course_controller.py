# app/controllers/course_controller.py
from datetime import date, datetime
from flask import Blueprint, render_template, request, session as flask_session, jsonify, session  # Renommez l'import
from sqlalchemy.orm import joinedload

from app.database.connDB import db
from app.models.course import CoursModel
from app.models.course_session import CoursSessionModel
from app.services.course_service import CoursService
from app.auth.decorators import login_required

cours_bp = Blueprint("cours", __name__, url_prefix="/cours")


def enseignant_or_delegue_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if flask_session.get("role") not in ["ensg", "délégué"]:  # Utilisez flask_session
            return jsonify({"error": "Accès refusé"}), 403
        return f(*args, **kwargs)

    return decorated


# ==================== ROUTES EXISTANTES ====================

# Version optimisée
@cours_bp.route("/")
@login_required
@enseignant_or_delegue_required
def list_courses():
    """Affiche les cours d'aujourd'hui groupés par filière"""
    today = date.today()

    # Récupérer directement les cours avec sessions d'aujourd'hui
    from app.models.course import CoursModel
    from app.models.course_session import CoursSessionModel
    from app.database.connDB import db

    user_id = flask_session["user_id"]  # Utilisez flask_session

    # Requête qui joint cours et sessions
    results = (
        db.session.query(CoursModel, CoursSessionModel)
        .join(CoursSessionModel, CoursSessionModel.cours_id == CoursModel.id)
        .filter(
            CoursModel.user_id == user_id,
            CoursSessionModel.date == today
        )
        .all()
    )

    # Organiser les résultats par cours
    courses_dict = {}
    for cours, session_obj in results:  # Renommez 'session' en 'session_obj'
        if cours.id not in courses_dict:
            courses_dict[cours.id] = {
                'id': cours.id,
                'nom': cours.nom,
                'filiere': cours.filiere,
                'semestre': cours.semestre,
                'sessions': []
            }
        courses_dict[cours.id]['sessions'].append(session_obj)

    # Convertir en liste
    today_courses = list(courses_dict.values())

    # Grouper par filière
    courses_by_filiere = {}
    for course in today_courses:
        filiere = course['filiere']
        if filiere not in courses_by_filiere:
            courses_by_filiere[filiere] = []
        courses_by_filiere[filiere].append(course)

    return render_template("courses/list.html",
                           courses_by_filiere=courses_by_filiere,
                           today=today.strftime("%d/%m/%Y"))


@cours_bp.route("/create", methods=["POST"])
@login_required
@enseignant_or_delegue_required
def create_course():
    sessions = []
    i = 1
    while request.form.get(f"date{i}"):
        sessions.append({
            "date": request.form.get(f"date{i}"),
            "seance": request.form.get(f"seance{i}")
        })
        i += 1

    cours = CoursService.create_course(
        user_id=flask_session["user_id"],  # Utilisez flask_session
        nom=request.form["nom"],
        filiere=request.form["filiere"],
        semestre=request.form["semestre"],
        sessions=sessions
    )
    return jsonify(success=True, id=cours.id)


@cours_bp.route("/<int:cours_id>/edit", methods=["POST"])
@login_required
@enseignant_or_delegue_required
def edit_course(cours_id):
    sessions = []
    i = 1
    while request.form.get(f"date{i}"):
        sessions.append({
            "date": request.form.get(f"date{i}"),
            "seance": request.form.get(f"seance{i}")
        })
        i += 1

    CoursService.update_course(
        cours_id,
        flask_session["user_id"],  # Utilisez flask_session
        request.form["nom"],
        request.form["filiere"],
        request.form["semestre"],
        sessions
    )
    return jsonify(success=True)


@cours_bp.route("/<int:cours_id>/delete", methods=["POST"])
@login_required
@enseignant_or_delegue_required
def delete_course(cours_id):
    CoursService.delete_course(cours_id, flask_session["user_id"])  # Utilisez flask_session
    return jsonify(success=True)


@cours_bp.route("/<int:cours_id>/json")
@login_required
def get_course_json(cours_id):
    cours = CoursService.get_course(cours_id, flask_session["user_id"])
    if not cours:
        return jsonify({})

    # Utilisez to_dict() ou accédez directement
    return jsonify({
        "id": cours.id,
        "nom": cours.nom,
        "filiere": cours.filiere,
        "semestre": cours.semestre,
        "sessions": [
            {
                "date": cs.date.strftime("%Y-%m-%d"),
                "seance": cs.seance
            } for cs in cours.sessions  # Utilisez la propriété
        ]
    })



@cours_bp.route("/api/<int:cours_id>/sessions/today", methods=['GET'])
@login_required
@enseignant_or_delegue_required
def get_sessions_by_course_today(cours_id):
    """Récupère les sessions d'un cours spécifique qui sont prévues aujourd'hui"""
    try:
        today = date.today()
        cours = CoursModel.query.get(cours_id)
        if not cours:
            return jsonify({"error": "Cours non trouvé"}), 404

        # Récupérer uniquement les sessions d'aujourd'hui
        sessions = (
            CoursSessionModel.query
            .filter_by(cours_id=cours_id)
            .filter(CoursSessionModel.date == today)
            .all()
        )

        sessions_data = []
        for session_obj in sessions:
            sessions_data.append({
                "id": session_obj.id,
                "cours_id": session_obj.cours_id,
                "date": session_obj.date.isoformat() if session_obj.date else None,
                "seance": session_obj.seance,
                "formatted_date": session_obj.date.strftime("%d/%m/%Y") if session_obj.date else None,
                "cours_nom": cours.nom,
                "filiere": cours.filiere,
                "semestre": cours.semestre,
                "display_text": f"Séance {session_obj.seance}"
            })

        return jsonify({
            "cours": {
                "id": cours.id,
                "nom": cours.nom,
                "filiere": cours.filiere,
                "semestre": cours.semestre
            },
            "today": today.strftime("%Y-%m-%d"),
            "sessions": sessions_data,
            "count": len(sessions_data)
        }), 200
    except Exception as e:
        print(f"Erreur dans get_sessions_by_course_today: {e}")
        return jsonify({"error": str(e)}), 500

@cours_bp.route("/today/filieres")
@login_required
@enseignant_or_delegue_required
def get_available_filieres_today():
    """Retourne les filières qui ont des cours aujourd'hui pour l'utilisateur"""
    filieres = CoursService.get_available_filieres_for_today(flask_session["user_id"])  # Utilisez flask_session
    return jsonify(filieres)


@cours_bp.route("/today/json")
@login_required
@enseignant_or_delegue_required
def get_today_courses():
    filiere = request.args.get("filiere")
    if not filiere:
        return jsonify({"error": "Filière non spécifiée"}), 400
    courses = CoursService.get_today_courses_by_filiere(
        user_id=flask_session["user_id"],  # Utilisez flask_session
        filiere=filiere
    )
    return jsonify(courses)


# ==================== NOUVELLES ROUTES API ====================

@cours_bp.route("/api/filieres/today", methods=['GET'])
@login_required
@enseignant_or_delegue_required
def get_filieres_today():
    """Récupère les filières distinctes qui ont des cours aujourd'hui"""
    try:
        today = date.today()
        # Récupérer les filières distinctes des cours qui ont des sessions aujourd'hui
        filieres = (
            db.session.query(CoursModel.filiere)
            .distinct()
            .join(CoursSessionModel)
            .filter(CoursSessionModel.date == today)
            .all()
        )
        filiere_list = [f[0] for f in filieres if f[0]]
        return jsonify({
            "filieres": sorted(filiere_list),
            "count": len(filiere_list),
            "today": today.strftime("%Y-%m-%d")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@cours_bp.route("/api/filiere/<filiere>/cours/today", methods=['GET'])
@login_required
@enseignant_or_delegue_required
def get_cours_by_filiere_today(filiere):
    """Récupère tous les cours d'une filière spécifique qui ont des sessions aujourd'hui"""
    try:
        today = date.today()

        # Récupérer les cours de la filière qui ont des sessions aujourd'hui
        # Sans utiliser joinedload car la relation n'existe pas
        cours = (
            CoursModel.query
            .filter(CoursModel.filiere == filiere)
            .all()
        )

        cours_data = []
        for c in cours:
            # Récupérer les sessions d'aujourd'hui pour ce cours
            sessions_today = CoursSessionModel.query.filter_by(
                cours_id=c.id,
                date=today
            ).all()

            session_count = len(sessions_today)

            if session_count > 0:
                cours_data.append({
                    "id": c.id,
                    "nom": c.nom,
                    "filiere": c.filiere,
                    "semestre": c.semestre,
                    "session_count": session_count,
                    "has_sessions": session_count > 0,
                    "sessions_today": [
                        {
                            "id": s.id,
                            "date": s.date.strftime("%Y-%m-%d"),
                            "seance": s.seance
                        } for s in sessions_today
                    ]
                })

        if not cours_data:
            return jsonify({
                "filiere": filiere,
                "today": today.strftime("%Y-%m-%d"),
                "cours": [],
                "count": 0,
                "message": f"Aucun cours trouvé pour la filière {filiere} aujourd'hui"
            }), 200

        return jsonify({
            "filiere": filiere,
            "today": today.strftime("%Y-%m-%d"),
            "cours": cours_data,
            "count": len(cours_data)
        }), 200
    except Exception as e:
        print(f"Erreur dans get_cours_by_filiere_today: {e}")
        return jsonify({"error": str(e)}), 500


@cours_bp.route('/diagnostic', methods=['GET'])
@login_required
@enseignant_or_delegue_required
def diagnostic():
    """Route de diagnostic pour vérifier l'état des données"""
    try:
        # Compter les cours
        cours_count = CoursModel.query.count()
        sessions_count = CoursSessionModel.query.count()

        # Récupérer quelques exemples
        sample_cours = CoursModel.query.limit(5).all()
        sample_sessions = CoursSessionModel.query.limit(5).all()

        # Préparer les données
        cours_data = []
        for c in sample_cours:
            # Compter les sessions pour ce cours
            session_count = CoursSessionModel.query.filter_by(cours_id=c.id).count()
            cours_data.append({
                "id": c.id,
                "nom": c.nom,
                "filiere": c.filiere,
                "semestre": c.semestre,
                "sessions_count": session_count
            })

        sessions_data = []
        for s in sample_sessions:
            # Récupérer le nom du cours
            cours_nom = "N/A"
            cours = CoursModel.query.get(s.cours_id)
            if cours:
                cours_nom = cours.nom

            sessions_data.append({
                "id": s.id,
                "cours_id": s.cours_id,
                "date": s.date.isoformat() if s.date else None,
                "seance": s.seance,
                "cours_nom": cours_nom
            })

        # Vérifier si une session existe avec l'ID 1
        session_1 = CoursSessionModel.query.get(1)

        return jsonify({
            "statistics": {
                "total_cours": cours_count,
                "total_sessions": sessions_count
            },
            "sample_cours": cours_data,
            "sample_sessions": sessions_data,
            "test_session_1": {
                "exists": session_1 is not None,
                "details": {
                    "id": session_1.id if session_1 else None,
                    "cours_id": session_1.cours_id if session_1 else None,
                    "date": session_1.date.isoformat() if session_1 and session_1.date else None,
                    "seance": session_1.seance if session_1 else None
                }
            },
            "endpoints_available": [
                "/cours/diagnostic (cette route)",
                "/cours/api/filieres/today (GET)",
                "/cours/api/filiere/<filiere>/cours/today (GET)",
                "/cours/api/<id>/sessions/today (GET)",
                "/cours/<id>/json (GET)",
                "/cours/create (POST)",
                "/cours/<id>/edit (POST)",
                "/cours/<id>/delete (POST)"
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Dans votre cours_controller.py
@cours_bp.route("/api/teacher/today", methods=["GET"])
@login_required
def api_teacher_courses_today():
    """API pour vérifier si l'enseignant a des cours aujourd'hui"""
    try:
        if session.get('role') != 'enseignant':
            return jsonify({
                "has_courses": False,
                "message": "Réservé aux enseignants"
            })

        enseignant_id = session.get('user_id')
        aujourdhui = datetime.now().date()

        from app.models.course import CoursModel
        from app.models.course_session import CoursSessionModel

        # Compter les sessions de l'enseignant pour aujourd'hui
        session_count = CoursSessionModel.query \
            .join(CoursModel, CoursSessionModel.cours_id == CoursModel.id) \
            .filter(
            CoursModel.user_id == enseignant_id,
            CoursSessionModel.date == aujourdhui
        ) \
            .count()

        # Compter les cours distincts
        cours_ids = CoursSessionModel.query \
            .join(CoursModel, CoursSessionModel.cours_id == CoursModel.id) \
            .filter(
            CoursModel.user_id == enseignant_id,
            CoursSessionModel.date == aujourdhui
        ) \
            .with_entities(CoursModel.id) \
            .distinct() \
            .count()

        return jsonify({
            "has_courses": session_count > 0,
            "session_count": session_count,
            "course_count": cours_ids,
            "date": aujourdhui.strftime("%d/%m/%Y"),
            "message": f"Vous avez {session_count} session(s) pour {cours_ids} cours aujourd'hui" if session_count > 0 else "Aucun cours programmé pour aujourd'hui"
        })

    except Exception as e:
        return jsonify({
            "has_courses": False,
            "error": str(e)
        }), 500