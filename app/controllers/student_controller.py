from flask import Blueprint, render_template, request, redirect, url_for, session, abort, jsonify
from app.services.student_service import EtudiantService
from app.auth.decorators import login_required
from functools import wraps

student_bp = Blueprint("students", __name__, url_prefix="/students")


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


# ========================
# LISTE DES ÉTUDIANTS (HEAD)
# ========================
@student_bp.route("/")
@login_required
@head_required
def list_students():
    students = EtudiantService.get_all()
    return render_template("students/list.html", students=students)


# ========================
# CRÉATION ÉTUDIANT (HEAD)
# ========================
# Dans create_student() - REMPLACEZ cette partie
@student_bp.route("/create", methods=["GET", "POST"])
@login_required
@head_required
def create_student():
    if request.method == "POST":
        # Données du formulaire
        data = {
            "matricule": request.form["matricule"],
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "filiere": request.form.get("filiere", ""),
            "annee": request.form.get("annee", "")
        }

        # CORRECTION ICI: Récupérer les bons fichiers
        # Selon le debug, les noms sont: "profil-avant", "profil", "profil-droite"
        files = {
            "profil-avant": request.files.get("profil-avant"),
            "profil-gauche": request.files.get("profil-gauche"),  # Note: HTML a name="profil" pour gauche
            "profil-droite": request.files.get("profil-droite")
        }

        print(f"[CONTROLLER] Fichiers extraits: {list(files.keys())}")

        # Vérifier que tous les fichiers sont présents
        for key, file in files.items():
            if not file or file.filename == '':
                return f"Le fichier {key} est requis", 400

        EtudiantService.create(data, files)
        return redirect(url_for("students.list_students"))

    # ... reste du code
# ========================
# MODIFICATION (HEAD)
# ========================
@student_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@head_required
def edit_student(student_id):
    student = EtudiantService.get_by_id(student_id)
    if not student:
        abort(404)

    if request.method == "POST":
        data = {
            "matricule": request.form["matricule"],
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "filiere": request.form.get("filiere"),
            "annee": request.form.get("annee")
        }
        files = {
            "photo": request.files.get("photo")
        }
        files = {k: v for k, v in files.items() if v}
        EtudiantService.update(student, data, files)
        return redirect(url_for("students.list_students"))

    # Si fetch AJAX pour modal
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("students/form.html", student=student)

    return render_template("students/form.html", student=student)


# ========================
# SUPPRESSION (HEAD)
# ========================
@student_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
@head_required
def delete_student(student_id):
    student = EtudiantService.get_by_id(student_id)
    if not student:
        abort(404)
    EtudiantService.delete(student)
    return redirect(url_for("students.list_students"))

# ========================
# RENVOIE DE JSON
# ========================
@student_bp.route("/<int:student_id>/json")
@login_required
@head_required
def get_student_json(student_id):
    student = EtudiantService.get_by_id(student_id)
    if not student:
        return {}, 404
    return {
        "nom": student.nom,
        "prenom": student.prenom,
        "matricule": student.matricule,
        "filiere": student.filiere,
        "annee": student.annee
    }
