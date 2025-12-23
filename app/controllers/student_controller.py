from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from app.services.student_service import EtudiantService
from app.auth.decorators import login_required

student_bp = Blueprint("students", __name__, url_prefix="/students")

# Définir les décorateurs pour les rôles
def head_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        role = session.get("role")
        if role != "respoFiliere":
            abort(403)  # accès interdit si pas responsable
        return f(*args, **kwargs)
    return decorated

def enseignant_or_delegue_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        role = session.get("role")
        if role not in ["ensg", "delegue", "head"]:
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ========================
# LISTE (TOUS LES ROLES)
# ========================
@student_bp.route("/")
@login_required
@enseignant_or_delegue_required
def list_students():
    students = EtudiantService.get_all()
    role = session.get("role")
    return render_template("students/list.html", students=students, role=role)

# ========================
# CRÉATION (HEAD SEUL)
# ========================
@student_bp.route("/create", methods=["GET", "POST"])
@login_required
@head_required
def create_student():
    if request.method == "POST":
        data = {
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "matricule": request.form["matricule"],
            "filiere": request.form["filiere"],
            "annee": request.form["annee"]
        }
        files = {
            "avant": request.files["avant"],
            "gauche": request.files["gauche"],
            "droite": request.files["droite"]
        }
        EtudiantService.create(data, files)
        return redirect(url_for("students.list_students"))
    return render_template("students/form.html", student=None)

# ========================
# ÉDITION (HEAD SEUL)
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
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "matricule": request.form["matricule"],
            "filiere": request.form["filiere"],
            "annee": request.form["annee"]
        }
        files = {
            "avant": request.files.get("avant"),
            "gauche": request.files.get("gauche"),
            "droite": request.files.get("droite")
        }
        # Ne pas remplacer les photos si fichiers vides
        files = {k:v for k,v in files.items() if v}
        EtudiantService.update(student, data, files)
        return redirect(url_for("students.list_students"))

    return render_template("students/form.html", student=student)

# ========================
# SUPPRESSION (HEAD SEUL)
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
