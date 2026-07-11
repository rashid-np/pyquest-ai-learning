from flask import Blueprint, request, session
from models.submission import Submission
from models.user import User
from services.submission_service import process_submission
from utils.validators import validate_user_answer
from utils.responses import success, error

submissions_bp = Blueprint("submissions", __name__, url_prefix="/api/submissions")


@submissions_bp.route("/", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id") or session.get("user_id")
    if not user_id:
        return error("user_id is required (or log in first).", 400)

    question_id = data.get("question_id")
    if not question_id:
        return error("question_id is required.", 400)

    try:
        user_answer = validate_user_answer(data.get("answer"))
    except ValueError as e:
        return error(str(e), 400)

    request_hint = bool(data.get("request_hint", False))

    try:
        result = process_submission(
            user_id=int(user_id),
            question_id=int(question_id),
            user_answer=user_answer,
            request_hint=request_hint
        )
    except ValueError as e:
        return error(str(e), 404)
    except Exception as e:
        return error(f"Submission processing failed: {str(e)}", 500)

    message = "Correct! Well done." if result["correct"] else "Incorrect. Keep trying!"
    return success(data=result, message=message)


@submissions_bp.route("/stats", methods=["GET"])
def get_stats():
    """Return aggregate stats for a user — used by the dashboard."""
    user_id = request.args.get("user_id") or session.get("user_id")
    if not user_id:
        return error("user_id required.", 400)

    subs = Submission.query.filter_by(user_id=int(user_id)).all()
    user = User.query.get(int(user_id))

    total       = len(subs)
    correct     = sum(1 for s in subs if s.correct)
    incorrect   = total - correct
    hints_used  = sum(1 for s in subs if s.hint_used)
    total_score = user.total_score if user else 0
    streak      = user.streak      if user else 0

    # Per-topic breakdown
    topic_map = {}
    for s in subs:
        t = s.topic or "Unknown"
        if t not in topic_map:
            topic_map[t] = {"correct": 0, "total": 0}
        topic_map[t]["total"] += 1
        if s.correct:
            topic_map[t]["correct"] += 1

    return success(data={
        "total":       total,
        "correct":     correct,
        "incorrect":   incorrect,
        "hints_used":  hints_used,
        "total_score": total_score,
        "streak":      streak,
        "topics":      topic_map,
    })


@submissions_bp.route("/<int:submission_id>", methods=["GET"])
def get_submission(submission_id: int):
    sub = Submission.query.get(submission_id)
    if not sub:
        return error(f"Submission {submission_id} not found.", 404)
    return success(data=sub.to_dict())


@submissions_bp.route("/user/<int:user_id>", methods=["GET"])
def list_user_submissions(user_id: int):
    topic = request.args.get("topic")
    limit = min(int(request.args.get("limit", 20)), 100)

    query = Submission.query.filter_by(user_id=user_id)
    if topic:
        query = query.filter_by(topic=topic)

    submissions = query.order_by(Submission.id.desc()).limit(limit).all()
    return success(data=[s.to_dict() for s in submissions])
