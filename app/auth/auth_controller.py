from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from app.auth.auth_service import AuthService
from app.auth.decorators import login_required, responsable_required
from app.services.user_service import UserService
from app.models.enum import UserRole

bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------------- LOGIN ----------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        try:
            user = AuthService.login(email, password)

            # Redirection selon le rôle
            if user.role == UserRole.HEAD.value:
                return redirect(url_for("dashboard.head_dashboard"))
            elif user.role == UserRole.ENSEIGNANT.value:
                return redirect(url_for("dashboard.enseignant_dashboard"))
            elif user.role == UserRole.DELEGUE.value:
                return redirect(url_for("dashboard.delegue_dashboard"))

        except Exception:
            flash("Login ou identifiant incorrect", "error")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# ---------------- REGISTER (Responsable uniquement) ----------------
@bp.route("/register", methods=["GET", "POST"])
@login_required
@responsable_required
def register():
    if request.method == "POST":
        UserService.create_user(
            nom=request.form["nom"],
            prenom=request.form["prenom"],
            email=request.form["email"],
            password=request.form["password"],
            role=request.form["role"],
            filiere=request.form.get("filiere")
        )
        flash("Utilisateur créé avec succès", "info")
        return redirect(url_for("dashboard.head_dashboard"))

    return render_template(
        "register.html",
        roles=[UserRole.ENSEIGNANT.value, UserRole.DELEGUE.value]
    )


# ---------------- LOGOUT ----------------
# Dans votre blueprint auth.py
@bp.route("/logout")
def logout():
    AuthService.logout()
    return redirect(url_for("auth.login"))
