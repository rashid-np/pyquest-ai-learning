"""
Questions route — generates and saves questions
"""

from flask import Blueprint, request
from database import db
from models.question import Question
from services.agents import question_generator_agent
from utils.responses import success, error
from utils.validators import validate_topic, validate_difficulty

questions_bp = Blueprint("questions", __name__, url_prefix="/api/questions")


@questions_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}

    try:
        topic      = validate_topic(data.get("topic", ""))
        difficulty = validate_difficulty(data.get("difficulty", ""))
    except ValueError as e:
        return error(str(e), 400)

    # Prevent duplicate questions for this topic/difficulty
    past = Question.query.filter_by(
        topic=topic, difficulty=difficulty
    ).order_by(Question.id.desc()).limit(20).all()
    past_titles = [q.title for q in past]

    try:
        qdata = question_generator_agent(
            topic=topic, difficulty=difficulty, past_titles=past_titles
        )
    except ValueError as e:
        return error(str(e), 500)

    question = Question(
        topic             = qdata["topic"],
        difficulty        = qdata["difficulty"],
        title             = qdata["title"],
        problem_statement = qdata["problem_statement"],
        template_code     = qdata["template_code"],
        correct_answer    = qdata["correct_answer"],
        expected_output   = qdata.get("expected_output", ""),
    )
    question.test_cases   = qdata.get("test_cases", [])
    question.answers_list = qdata.get("answers_list", [qdata["correct_answer"]])

    db.session.add(question)
    db.session.commit()

    return success(data=question.to_dict(), message="Question generated.", status=201)


@questions_bp.route("/", methods=["GET"])
def list_questions():
    topic      = request.args.get("topic")
    difficulty = request.args.get("difficulty")
    q = Question.query
    if topic:      q = q.filter_by(topic=topic)
    if difficulty: q = q.filter_by(difficulty=difficulty)
    return success(data=[q.to_dict() for q in q.order_by(Question.id.desc()).limit(50).all()])
