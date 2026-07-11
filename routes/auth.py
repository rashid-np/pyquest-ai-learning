"""
Auth routes — separate register vs login with password verification
"""
from flask import Blueprint, request, session
from database import db
from models.user import User
from utils.responses import success, error

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or len(username) < 2:
        return error("Username must be at least 2 characters.", 400)
    if len(username) > 30:
        return error("Username must be at most 30 characters.", 400)
    if not password or len(password) < 6:
        return error("Password must be at least 6 characters.", 400)

    existing = User.query.filter_by(username=username).first()
    if existing:
        return error("Username already exists. Please sign in instead.", 409)

    user = User(username=username, total_score=0, streak=0)
    user.set_password(password)
    db.session.add(user)

    from datetime import datetime
    user.last_seen = datetime.utcnow()
    db.session.commit()

    session["user_id"] = user.id
    session.permanent  = True

    return success(data={
        "id":             user.id,
        "username":       user.username,
        "total_score":    0,
        "streak":         0,
        "topic_progress": "{}",
        "is_new":         True,
    }, message="Account created.", status=201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or len(username) < 2:
        return error("Username is required.", 400)
    if not password:
        return error("Password is required.", 400)

    user = User.query.filter_by(username=username).first()
    if not user:
        return error("No account found with that username. Please create an account first.", 404)
    if not user.check_password(password):
        return error("Incorrect password. Please try again.", 401)

    from datetime import datetime
    user.last_seen = datetime.utcnow()
    db.session.commit()

    session["user_id"] = user.id
    session.permanent  = True

    return success(data={
        "id":             user.id,
        "username":       user.username,
        "total_score":    user.total_score or 0,
        "streak":         user.streak or 0,
        "topic_progress": user.topic_progress or "{}",
        "is_new":         False,
    }, message="Signed in.")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return success(message="Logged out.")


@auth_bp.route("/save-progress", methods=["POST"])
def save_progress():
    """Save topic progress JSON to DB so it persists across browsers/devices."""
    data    = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or session.get("user_id")
    if not user_id:
        return error("user_id required.", 400)
    user = User.query.get(user_id)
    if not user:
        return error("User not found.", 404)
    progress_json = data.get("progress", "{}")
    import json
    try:
        json.loads(progress_json)  # validate it's valid JSON
    except Exception:
        return error("Invalid progress data.", 400)
    user.topic_progress = progress_json
    db.session.commit()
    return success(message="Progress saved.")


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return error("Not logged in.", 401)
    user = User.query.get(user_id)
    if not user:
        return error("User not found.", 404)
    return success(data={
        "id":             user.id,
        "username":       user.username,
        "total_score":    user.total_score or 0,
        "streak":         user.streak or 0,
        "topic_progress": user.topic_progress or "{}",
    })


@auth_bp.route("/score", methods=["POST"])
def update_score():
    data    = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or session.get("user_id")
    if not user_id:
        return error("user_id required.", 400)
    user = User.query.get(user_id)
    if not user:
        return error("User not found.", 404)
    add_score = int(data.get("score", 0))
    streak    = data.get("streak")
    if add_score > 0:
        user.total_score = (user.total_score or 0) + add_score
    if streak is not None:
        user.streak = int(streak)
    db.session.commit()
    return success(data={"total_score": user.total_score, "streak": user.streak})
