"""
Submission Service — 4-Agent Pipeline
=======================================
Agent 1 → Question Generation      (in questions.py)
Agent 2 → Sandbox Code Analysis    (runs code + 2-line explanation)
Agent 3 → LLM Answer Verifier      (primary correctness checker)
Agent 4 → Hint Generation          (costs -10 pts)

User progress (score + streak) saved to DB on every submission.
"""

from database import db
from models.question import Question
from models.submission import Submission
from models.user import User
from services.agents import (
    sandbox_analysis_agent,
    llm_verifier_agent,
    hint_generator_agent,
)

_SCORE_TABLE = {
    ("easy",   1): 100, ("easy",   2): 60,  ("easy",   3): 30,
    ("medium", 1): 150, ("medium", 2): 90,  ("medium", 3): 50,
    ("hard",   1): 200, ("hard",   2): 120, ("hard",   3): 70,
}


def _calc_score(difficulty: str, attempts: int,
                correct: bool, hint_used: bool) -> int:
    if not correct:
        return 0
    base = _SCORE_TABLE.get((difficulty.lower(), min(attempts, 3)), 30)
    if hint_used:
        base = max(0, base - 10)   # -10 pts for using hint
    return base


def _parse_answers(user_answer: str, num_blanks: int) -> list:
    """
    Parse ||| separated answers from frontend.
    "split() ||| +=" -> ["split()", "+="]
    """
    if num_blanks == 1:
        return [user_answer.strip()]
    parts = [p.strip() for p in user_answer.split("|||")]
    while len(parts) < num_blanks:
        parts.append("")
    return parts[:num_blanks]


def process_submission(user_id: int, question_id: int,
                       user_answer: str,
                       request_hint: bool = False) -> dict:

    question = Question.query.get(question_id)
    if not question:
        raise ValueError(f"Question {question_id} not found.")

    # Attempt count — also block re-scoring if already solved correctly
    existing = Submission.query.filter_by(
        user_id=user_id, question_id=question_id
    ).order_by(Submission.id.desc()).first()
    attempts = (existing.attempts + 1) if existing else 1

    # If user already answered this question correctly, no more score awarded
    already_correct = Submission.query.filter_by(
        user_id=user_id, question_id=question_id, correct=True
    ).first() is not None

    # Parse answers
    answers_list = question.answers_list or [question.correct_answer]
    num_blanks   = len(answers_list)
    user_answers = _parse_answers(user_answer, num_blanks)

    # ── AGENT 2: Sandbox Code Analysis ───────────────────────
    sandbox_result = sandbox_analysis_agent(
        template_code   = question.template_code,
        user_answers    = user_answers,
        expected_output = question.expected_output or "",
        topic           = question.topic,
    )

    # ── AGENT 3: LLM Verifier (primary checker) ───────────────
    llm_result = llm_verifier_agent(
        topic             = question.topic,
        difficulty        = question.difficulty,
        problem_statement = question.problem_statement,
        template_code     = question.template_code,
        correct_answers   = answers_list,
        user_answers      = user_answers,
        sandbox_result    = sandbox_result,
    )

    # Final verdict: either sandbox OR LLM says correct → correct
    correct = sandbox_result["sandbox_passed"] or llm_result["is_correct"]

    # ── AGENT 4: Hint Generation ──────────────────────────────
    hint_text = None
    hint_used = False
    if not correct and request_hint:
        hint_used = True
        hint_text = hint_generator_agent(
            topic               = question.topic,
            difficulty          = question.difficulty,
            problem_statement   = question.problem_statement,
            template_code       = question.template_code,
            user_answers        = user_answers,
            sandbox_explanation = sandbox_result.get("explanation", ""),
            llm_verdict         = llm_result.get("verdict", ""),
        )

    # ── Score (hint deducts -10 pts) ─────────────────────────
    # No score if question was already answered correctly before
    if already_correct:
        score = 0
    else:
        score = _calc_score(question.difficulty, attempts, correct, hint_used)

    # ── Save Submission ───────────────────────────────────────
    submission = Submission(
        user_id     = user_id,
        question_id = question_id,
        topic       = question.topic,
        user_answer = user_answer,
        correct     = correct,
        score       = score,
        attempts    = attempts,
        hint_used   = hint_used,
        hint_text   = hint_text,
    )
    db.session.add(submission)

    # ── Save User Progress to DB ──────────────────────────────
    user = User.query.get(user_id)
    if user:
        if correct and score > 0 and not already_correct:
            user.total_score = (user.total_score or 0) + score
            user.streak      = (user.streak or 0) + 1
        elif not correct and not already_correct:
            user.streak = 0

        # Hint penalty: always deduct 10 from total_score when hint is used,
        # regardless of correctness (hint requested = -10 pts, floor 0)
        if hint_used:
            user.total_score = max(0, (user.total_score or 0) - 10)

        from datetime import datetime
        user.last_seen = datetime.utcnow()

    db.session.commit()

    return {
        "submission_id":    submission.id,
        "correct":          correct,
        "score":            score,
        "attempts":         attempts,
        "num_blanks":       num_blanks,
        "already_correct":  already_correct,
        # Source of truth — always read from DB
        "total_score":      user.total_score if user else 0,
        "streak":           user.streak      if user else 0,
        # Agent 2 — sandbox
        "sandbox_passed":      sandbox_result["sandbox_passed"],
        "user_output":         sandbox_result["user_output"],
        "expected_output":     sandbox_result["expected_output"],
        "runtime_error":       sandbox_result["runtime_error"],
        "sandbox_explanation": sandbox_result["explanation"],
        # Agent 3 — LLM
        "llm_verdict":    llm_result["verdict"],
        "is_alternative": llm_result["is_alternative"],
        # Agent 4 — hint
        "hint_used": hint_used,
        "hint":      hint_text,
    }
