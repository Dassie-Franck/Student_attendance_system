from flask import Blueprint, render_template, request, redirect, url_for, session, abort, jsonify, flash
from app.services.user_service import UserService
from functools import wraps

bp = Blueprint("user", __name__, url_prefix="/users")


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
# LISTE DES UTILISATEURS (HEAD)
# ========================
@bp.route("/")
@head_required
def list_users():
    try:
        users = UserService.get_all()
        return render_template("users/list.html", users=users)
    except Exception as e:
        flash(f"Erreur: {str(e)}", "danger")
        return render_template("users/list.html", users=[])


# ========================
# CRÉATION UTILISATEUR (HEAD)
# ========================
@bp.route("/create", methods=["GET", "POST"])
@head_required
def create_user():
    if request.method == "POST":
        try:
            data = {
                "nom": request.form["nom"],
                "prenom": request.form["prenom"],
                "email": request.form["email"],
                "password": request.form["password"],
                "role": request.form["role"],
                "filiere": request.form.get("filiere", "")
            }

            UserService.create(data)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": True, "message": "Utilisateur créé avec succès"})

            flash("Utilisateur créé avec succès!", "success")
            return redirect(url_for("user.list_users"))

        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": str(e)}), 400
            flash(f"Erreur: {str(e)}", "danger")
            return redirect(url_for("user.list_users"))

    # Si c'est un fetch AJAX pour modal
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("users/form.html", user=None)

    return render_template("users/form.html", user=None)


# ========================
# MODIFICATION (HEAD)
# ========================
@bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@head_required
def edit_user(user_id):
    user = UserService.get_by_id(user_id)
    if not user:
        abort(404)

    if request.method == "POST":
        try:
            data = {
                "nom": request.form["nom"],
                "prenom": request.form["prenom"],
                "email": request.form["email"],
                "role": request.form["role"],
                "filiere": request.form.get("filiere", "")
            }

            # Ajouter le mot de passe seulement s'il est fourni
            if request.form.get("password"):
                data["password"] = request.form["password"]

            UserService.update(user, data)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": True, "message": "Utilisateur modifié avec succès"})

            flash("Utilisateur modifié avec succès!", "success")
            return redirect(url_for("user.list_users"))

        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": str(e)}), 400
            flash(f"Erreur: {str(e)}", "danger")
            return redirect(url_for("user.list_users"))

    # Si fetch AJAX pour modal
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("users/form.html", user=user)

    return render_template("users/form.html", user=user)


# ========================
# SUPPRESSION (HEAD)
# ========================
@bp.route("/<int:user_id>/delete", methods=["POST"])
@head_required
def delete_user(user_id):
    try:
        user = UserService.get_by_id(user_id)
        if not user:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
            abort(404)

        # Empêcher la suppression de soi-même
        if session.get('user_id') == user.id:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": "Vous ne pouvez pas supprimer votre propre compte"}), 400
            flash("Vous ne pouvez pas supprimer votre propre compte", "danger")
            return redirect(url_for("user.list_users"))

        UserService.delete(user)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True, "message": "Utilisateur supprimé avec succès"})

        flash("Utilisateur supprimé avec succès!", "success")
        return redirect(url_for("user.list_users"))

    except Exception as e:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": str(e)}), 400
        flash(f"Erreur: {str(e)}", "danger")
        return redirect(url_for("user.list_users"))


# ========================
# RENVOIE DE JSON
# ========================
@bp.route("/<int:user_id>/json")
@head_required
def get_user_json(user_id):
    user = UserService.get_by_id(user_id)
    if not user:
        return jsonify({}), 404

    return jsonify({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "role": user.role,  # Retourne la valeur réelle ("respoFiliere", "ensg", "delegue")
        "filiere": user.filiere or ""
    })