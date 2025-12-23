from flask import Blueprint, render_template, session, abort, redirect, url_for
from app.services.user_service import UserService

dashboard_bp = Blueprint('dashboard', __name__)

def current_user():
    """Retourne l'objet UserModel du user connecté ou None si non connecté"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return UserService.get_user_by_id(user_id)

# -------------------- HEAD DASHBOARD --------------------
@dashboard_bp.route('/head')
def head_dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))
    if not UserService.is_responsable(user):
        abort(403)
    return render_template("dashboard/head_dashboard.html", user=user)

# -------------------- ENSEIGNANT DASHBOARD --------------------
@dashboard_bp.route('/enseignant')
def enseignant_dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))
    if not UserService.is_enseignant(user):
        abort(403)
    return render_template("dashboard/staff_dashboard.html", user=user)

# -------------------- DELEGUE DASHBOARD --------------------
@dashboard_bp.route('/delegue')
def delegue_dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))
    if not UserService.is_delegue(user):
        abort(403)
    return render_template("dashboard/delegue_dashboard.html", user=user)
