from functools import wraps
from flask import session, redirect, url_for, abort
from app.services.user_service import UserService
from app.models.enum import UserRole

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

def responsable_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.login"))

        user = UserService.get_by_id(user_id)
        if not user or user.role != UserRole.HEAD.value:
            abort(403)

        return f(*args, **kwargs)
    return decorated
