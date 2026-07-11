from database import db
from datetime import datetime


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    user_answer = db.Column(db.Text, nullable=False)
    correct = db.Column(db.Boolean, nullable=False, default=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    attempts = db.Column(db.Integer, nullable=False, default=1)
    hint_used = db.Column(db.Boolean, nullable=False, default=False)
    hint_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "topic": self.topic,
            "user_answer": self.user_answer,
            "correct": self.correct,
            "score": self.score,
            "attempts": self.attempts,
            "hint_used": self.hint_used,
            "hint_text": self.hint_text,
            "created_at": self.created_at.isoformat()
        }
