from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from app.services.course_service import CoursService
from app.models.enum import CourSession
from app.auth.decorators import login_required
from deepface import DeepFace
cours_bp = Blueprint("cours", __name__, url_prefix="/cours")


def enseignant_or_delegue_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") not in ["ensg", "delegue"]:
            abort(403)
        return f(*args, **kwargs)

    return decorated


@cours_bp.route("/")
@login_required
@enseignant_or_delegue_required
def list_courses():
    return render_template(
        "courses/list.html",
        courses=CoursService.get_all_courses()
    )


@cours_bp.route("/create", methods=["GET", "POST"])
@login_required
@enseignant_or_delegue_required
def create_course():
    if request.method == "POST":
        sessions = []

        for i in (1, 2):
            date = request.form.get(f"date{i}")
            seance = request.form.get(f"seance{i}")
            if date and seance:
                sessions.append({"date": date, "seance": seance})

        CoursService.create_course(
            session["user_id"],
            request.form["nom"],
            request.form["filiere"],
            request.form["semestre"],
            sessions
        )
        return redirect(url_for("cours.list_courses"))

    return render_template(
        "courses/form.html",
        seances=CourSession
    )


@cours_bp.route("/<int:cours_id>/edit", methods=["GET", "POST"])
@login_required
@enseignant_or_delegue_required
def edit_course(cours_id):
    cours = CoursService.get_course(cours_id)
    if not cours:
        abort(404)

    if request.method == "POST":
        sessions = []
        for i in (1, 2):
            date = request.form.get(f"date{i}")
            seance = request.form.get(f"seance{i}")
            if date and seance:
                sessions.append({"date": date, "seance": seance})

        CoursService.update_course(
            cours,
            request.form["nom"],
            request.form["filiere"],
            request.form["semestre"],
            sessions
        )
        return redirect(url_for("cours.list_courses"))

    return render_template(
        "courses/edit.html",
        cours=cours,
        seances=CourSession
    )


@cours_bp.route("/<int:cours_id>/delete", methods=["POST"])
@login_required
@enseignant_or_delegue_required
def delete_course(cours_id):
    cours = CoursService.get_course(cours_id)
    if not cours:
        abort(404)

    CoursService.delete_course(cours)
    return redirect(url_for("cours.list_courses"))
