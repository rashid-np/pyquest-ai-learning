"""
Question model — supports multiple blanks + expected_output
"""

import json
from database import db
from datetime import datetime


class Question(db.Model):
    __tablename__ = "questions"

    id                = db.Column(db.Integer, primary_key=True)
    topic             = db.Column(db.String(100), nullable=False)
    difficulty        = db.Column(db.String(20),  nullable=False)
    title             = db.Column(db.String(200), nullable=False)
    problem_statement = db.Column(db.Text,        nullable=False)
    template_code     = db.Column(db.Text,        nullable=False)
    correct_answer    = db.Column(db.Text,        nullable=False)
    expected_output   = db.Column(db.Text,        nullable=True)
    _answers_list     = db.Column("answers_list", db.Text, nullable=True)
    _test_cases       = db.Column("test_cases",   db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship("Submission", backref="question", lazy=True)

    @property
    def test_cases(self):
        try:
            return json.loads(self._test_cases) if self._test_cases else []
        except Exception:
            return []

    @test_cases.setter
    def test_cases(self, value):
        self._test_cases = json.dumps(value)

    @property
    def answers_list(self):
        try:
            if self._answers_list:
                return json.loads(self._answers_list)
        except Exception:
            pass
        return [self.correct_answer]

    @answers_list.setter
    def answers_list(self, value):
        self._answers_list = json.dumps(value)

    @property
    def num_blanks(self):
        return len(self.answers_list)

    def to_dict(self):
        return {
            "id":                self.id,
            "topic":             self.topic,
            "difficulty":        self.difficulty,
            "title":             self.title,
            "problem_statement": self.problem_statement,
            "template_code":     self.template_code,
            "correct_answer":    self.correct_answer,
            "expected_output":   self.expected_output,
            "answers_list":      self.answers_list,
            "num_blanks":        self.num_blanks,
            "test_cases":        self.test_cases,
            "created_at":        self.created_at.isoformat() if self.created_at else None,
        }