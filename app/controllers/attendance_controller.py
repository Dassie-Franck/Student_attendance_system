# app/controllers/attendance_controller.py
from functools import wraps

from flask import Blueprint, render_template, request, session, jsonify, make_response, abort, send_file
from app.auth.decorators import login_required
from app.database.connDB import db
from app.models.attendance import PresenceModel
from app.models.course_session import CoursSessionModel
from app.models.student import EtudiantModel
from app.services.attendance_service import AttendanceService
from datetime import datetime

from app.services.student_service import EtudiantService
from app.services.course_service import CoursService
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session as flask_session, jsonify, session  # Renommez l'import
attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


def enseignant_or_delegue_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if flask_session.get("role") not in ["ensg", "délégué"]:  # Utilisez flask_session
            return jsonify({"error": "Accès refusé"}), 403
        return f(*args, **kwargs)

    return decorated
# ========================
# DÉCORATEUR HEAD ONLY
# ========================
def head_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "respoFiliere":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@attendance_bp.route("/")
@login_required
@enseignant_or_delegue_required
def list_attendance():
    """Affiche la liste des présences d'aujourd'hui (Point 1)"""
    try:
        user_id = session.get("user_id")
        attendance_lists = AttendanceService.get_today_attendance(user_id)

        today = datetime.now().strftime("%d/%m/%Y")
        return render_template(
            "attendance/list.html",
            attendance_lists=attendance_lists,
            today=today
        )
    except Exception as e:
        print(f"Erreur: {e}")
        return render_template(
            "attendance/list.html",
            attendance_lists=[],
            today=datetime.now().strftime("%d/%m/%Y")
        )


@attendance_bp.route("/session/<int:session_id>")
@login_required
@enseignant_or_delegue_required
def session_attendance(session_id):
    """Affiche la liste de présence d'une session (Point 1)"""
    try:
        attendance_data = AttendanceService.get_session_attendance(session_id)
        return render_template(
            "attendance/session.html",
            attendance_data=attendance_data
        )
    except Exception as e:
        print(f"Erreur: {e}")
        return render_template(
            "attendance/session.html",
            attendance_data=None
        )


@attendance_bp.route("/update", methods=["POST"])
@login_required
@enseignant_or_delegue_required
def update_attendance():
    """Met à jour le statut de présence (Point 2)"""
    try:
        data = request.get_json()
        result = AttendanceService.update_attendance_status(data)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@attendance_bp.route("/export/csv/<int:session_id>")
@login_required
@enseignant_or_delegue_required
def export_csv(session_id):
    """Exporte la liste de présence en CSV (Point 3)"""
    try:
        csv_data = AttendanceService.generate_csv_data(session_id)
        if not csv_data:
            return jsonify({"error": "Aucune donnée à exporter"}), 404

        # Récupérer les infos pour le nom du fichier
        attendance_data = AttendanceService.get_session_attendance(session_id)
        if not attendance_data:
            return jsonify({"error": "Session non trouvée"}), 404

        # Créer le nom du fichier
        filename = f"presence_{attendance_data['cours_nom']}_{attendance_data['session_date'].strftime('%Y%m%d')}.csv"

        # Créer la réponse
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv; charset=utf-8"

        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========================
# CONSULTATION DES PRÉSENCES
# ========================
# Dans attendance_controller.py, modifiez consulter_presences()
# Dans attendance_controller.py, remplacez toute la fonction consulter_presences()
@attendance_bp.route("/consulter", methods=["GET"])
@login_required
@head_required
def consulter_presences():
    """Consultation des présences avec vue tableau"""
    try:
        # Récupérer les filtres
        cours_id = request.args.get('cours_id', '')
        selected_date = request.args.get('date', '')
        filiere = request.args.get('filiere', '')

        # Initialiser les données
        session_data = None
        etudiants = []
        presences_par_etudiant = {}
        presence_seance2 = {}
        stats = {
            'presents': 0,
            'absents': 0,
            'total_heures_absence': 0,
            'taux_presence': 0
        }

        if cours_id and selected_date:
            # Convertir la date
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d')

            # Récupérer la session pour la séance 1
            session = CoursSessionModel.query.filter_by(
                cours_id=cours_id,
                date=date_obj,
                seance='1'
            ).first()

            if session:
                # Récupérer le professeur
                from app.models.user import UserModel
                professeur = UserModel.query.get(session.cours.user_id)

                session_data = {
                    'id': session.id,
                    'date': session.date,
                    'seance': session.seance,
                    'cours': session.cours,
                    'professeur': professeur
                }

                # Récupérer tous les étudiants de la filière
                query = EtudiantModel.query
                if filiere:
                    query = query.filter_by(filiere=filiere)
                else:
                    # Si cours sélectionné, prendre la filière du cours
                    query = query.filter_by(filiere=session.cours.filiere)

                etudiants = query.order_by(EtudiantModel.nom, EtudiantModel.prenom).all()

                # Récupérer les présences pour la séance 1
                presences = PresenceModel.query.filter_by(
                    cours_session_id=session.id
                ).all()

                # Organiser par étudiant
                for presence in presences:
                    presences_par_etudiant[presence.etudiant_id] = presence
                    if presence.statut == 'P':
                        stats['presents'] += 1
                    else:
                        stats['absents'] += 1
                        stats['total_heures_absence'] += 2

                # Récupérer la session pour la séance 2
                session2 = CoursSessionModel.query.filter_by(
                    cours_id=cours_id,
                    date=date_obj,
                    seance='2'
                ).first()

                if session2:
                    # Récupérer les présences pour la séance 2
                    presences2 = PresenceModel.query.filter_by(
                        cours_session_id=session2.id
                    ).all()

                    for presence in presences2:
                        presence_seance2[presence.etudiant_id] = presence
                        if presence.statut == 'A':
                            stats['total_heures_absence'] += 2

                # Calculer le taux de présence
                total = stats['presents'] + stats['absents']
                if total > 0:
                    stats['taux_presence'] = round((stats['presents'] / total) * 100, 1)

        # Récupérer les données pour les filtres
        filieres = AttendanceService.get_filieres_disponibles()
        cours_list = CoursService.get_all_cours()

        return render_template("department_head/consulter.html",
                               session_data=session_data,
                               etudiants=etudiants,
                               presences_par_etudiant=presences_par_etudiant,
                               presence_seance2=presence_seance2,
                               stats=stats,
                               filieres=filieres,
                               cours_list=cours_list,
                               selected_cours=cours_id,
                               selected_date=selected_date,
                               selected_filiere=filiere)

    except ValueError as e:
        # Erreur de format de date
        print(f"[ERROR] Format de date invalide: {str(e)}")
        return render_template("department_head/consulter.html",
                               session_data=None,
                               etudiants=[],
                               presences_par_etudiant={},
                               presence_seance2={},
                               stats={'presents': 0, 'absents': 0, 'total_heures_absence': 0, 'taux_presence': 0},
                               filieres=AttendanceService.get_filieres_disponibles() if 'PresenceService' in globals() else [],
                               cours_list=CoursService.get_all_cours() if 'CoursService' in globals() else [],
                               selected_cours=cours_id,
                               selected_date=selected_date,
                               selected_filiere=filiere)

    except Exception as e:
        print(f"[ERROR] Erreur consultation présences: {str(e)}")
        import traceback
        traceback.print_exc()
        # Retourner une version simplifiée
        return render_template("department_head/consulter.html",
                               session_data=None,
                               etudiants=[],
                               presences_par_etudiant={},
                               presence_seance2={},
                               stats={'presents': 0, 'absents': 0, 'total_heures_absence': 0, 'taux_presence': 0},
                               filieres=[],
                               cours_list=[],
                               selected_cours=cours_id,
                               selected_date=selected_date,
                               selected_filiere=filiere,
                               error=str(e))
# ========================
# BILAN TRIMESTRIEL
# ========================
@attendance_bp.route("/bilan", methods=["GET"])
@login_required
@head_required
def bilan_trimestriel():
    """Bilan trimestriel pour tous les étudiants"""
    try:
        # Récupérer les filtres
        filiere = request.args.get('filiere', '')
        date_debut_str = request.args.get('date_debut', '')
        date_fin_str = request.args.get('date_fin', '')

        # Dates par défaut (trimestre en cours)
        today = datetime.now()
        if not date_debut_str:
            # Premier jour du trimestre (simplifié: premier jour du mois il y a 3 mois)
            date_debut = today.replace(day=1) - timedelta(days=90)
            date_debut_str = date_debut.strftime('%Y-%m-%d')
        else:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d')

        if not date_fin_str:
            date_fin_str = today.strftime('%Y-%m-%d')
            date_fin = today
        else:
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d')

        # Calculer le bilan pour chaque étudiant
        bilan_data = AttendanceService.calculer_bilan_trimestriel(
            filiere=filiere,
            date_debut=date_debut,
            date_fin=date_fin
        )

        # Statistiques générales
        stats = {
            'total_etudiants': len(bilan_data),
            'total_absences': sum(item['heures_absence'] for item in bilan_data),
            'moyenne_absences': sum(item['heures_absence'] for item in bilan_data) / len(
                bilan_data) if bilan_data else 0,
            'etudiants_parfait': len([item for item in bilan_data if item['heures_absence'] == 0]),
            'etudiants_critiques': len([item for item in bilan_data if item['heures_absence'] > 10])
        }

        filieres = AttendanceService.get_filieres_disponibles()

        return render_template("department_head/bilan.html",
                               bilan_data=bilan_data,
                               stats=stats,
                               filieres=filieres,
                               selected_filiere=filiere,
                               date_debut=date_debut_str,
                               date_fin=date_fin_str)

    except Exception as e:
        print(f"[ERROR] Erreur bilan trimestriel: {str(e)}")
        return render_template("department_head/error.html", message=str(e))


# ========================
# BILAN DÉTAILLÉ PAR ÉTUDIANT
# ========================
@attendance_bp.route("/bilan-etudiant/<int:etudiant_id>", methods=["GET"])
@login_required
@head_required
def bilan_etudiant_detail(etudiant_id):
    """Bilan détaillé pour un étudiant spécifique"""
    try:
        # Récupérer l'étudiant
        etudiant = EtudiantService.get_by_id(etudiant_id)
        if not etudiant:
            abort(404)

        # Récupérer les filtres
        date_debut_str = request.args.get('date_debut', '')
        date_fin_str = request.args.get('date_fin', '')

        # Dates par défaut (trimestre en cours)
        today = datetime.now()
        if not date_debut_str:
            date_debut = today.replace(day=1) - timedelta(days=90)
            date_debut_str = date_debut.strftime('%Y-%m-%d')
        else:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d')

        if not date_fin_str:
            date_fin_str = today.strftime('%Y-%m-%d')
            date_fin = today
        else:
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d')

        # Calculer le bilan détaillé
        bilan = AttendanceService.calculer_bilan_detaille_etudiant(
            etudiant_id=etudiant_id,
            date_debut=date_debut,
            date_fin=date_fin
        )

        return render_template("department_head/bilan_etudiant.html",
                               etudiant=etudiant,
                               bilan=bilan,
                               date_debut=date_debut_str,
                               date_fin=date_fin_str)

    except Exception as e:
        print(f"[ERROR] Erreur bilan étudiant: {str(e)}")
        return render_template("department_head/error.html", message=str(e))


# ========================
# EXPORT EXCEL
# ========================
@attendance_bp.route("/export-excel", methods=["GET"])
@login_required
@head_required
def export_excel():
    """Export des présences en Excel"""
    try:
        # Récupérer les filtres
        filiere = request.args.get('filiere', '')
        cours_id = request.args.get('cours_id', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')

        # Générer le fichier Excel
        excel_data = AttendanceService.generer_excel_presences(
            filiere=filiere,
            cours_id=cours_id,
            date_debut=date_debut,
            date_fin=date_fin
        )

        # Retourner le fichier Excel
        from io import BytesIO
        output = BytesIO()
        excel_data.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"presences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

    except Exception as e:
        print(f"[ERROR] Erreur export Excel: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ========================
# API JSON POUR FILTRES
# ========================
@attendance_bp.route("/api/cours-par-filiere", methods=["GET"])
@login_required
@head_required
def get_cours_by_filiere():
    """API pour récupérer les cours par filière (AJAX)"""
    filiere = request.args.get('filiere', '')
    if not filiere:
        return jsonify([])

    cours_list = CoursService.get_cours_by_filiere(filiere)
    return jsonify([{
        'id': cours.id,
        'nom': cours.nom,
        'professeur': f"{cours.user.prenom} {cours.user.nom}" if hasattr(cours, 'user') else "Non assigné"
    } for cours in cours_list])


# ========================
# STATISTIQUES RAPIDES
# ========================
@attendance_bp.route("/stats", methods=["GET"])
@login_required
@head_required
def stats_rapides():
    """Tableau de bord avec statistiques"""
    try:
        # Statistiques générales
        stats = AttendanceService.get_statistiques_globales()

        # Dernières présences enregistrées
        dernieres_presences = AttendanceService.get_dernieres_presences(limit=10)

        # Étudiants avec plus d'absences
        etudiants_absents = AttendanceService.get_etudiants_plus_absents(limit=5)

        return render_template("department_head/stats.html",
                               stats=stats,
                               dernieres_presences=dernieres_presences,
                               etudiants_absents=etudiants_absents)

    except Exception as e:
        print(f"[ERROR] Erreur statistiques: {str(e)}")
        return render_template("department_head/error.html", message=str(e))


@attendance_bp.route("/api/modifier-statut", methods=["POST"])
@login_required
@head_required
def api_modifier_statut():
    """API pour modifier le statut d'une présence"""
    try:
        data = request.get_json()
        presence_id = data.get('presence_id')
        nouveau_statut = data.get('statut')
        motif = data.get('motif', '')

        if not presence_id or not nouveau_statut:
            return jsonify({"success": False, "message": "Données manquantes"}), 400

        # Récupérer la présence
        presence = PresenceModel.query.get(presence_id)
        if not presence:
            return jsonify({"success": False, "message": "Présence non trouvée"}), 404

        # Mettre à jour le statut
        presence.statut = nouveau_statut
        if motif:
            # Si vous avez un champ pour le motif, l'utiliser
            if hasattr(presence, 'motif'):
                presence.motif = motif

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Statut mis à jour",
            "data": {
                "id": presence.id,
                "statut": presence.statut,
                "etudiant": f"{presence.etudiant.prenom} {presence.etudiant.nom}"
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
