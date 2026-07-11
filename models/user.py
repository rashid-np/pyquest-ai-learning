"""
User model — with password hashing for proper auth
Condition 5: User data properly stored with password
"""

from database import db
from datetime import datetime
import hashlib
import os


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # nullable for existing users
    total_score = db.Column(db.Integer, default=0)
    streak      = db.Column(db.Integer, default=0)
    topic_progress = db.Column(db.Text, nullable=True)  # JSON string of topic unlock progress
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen   = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship("Submission", backref="user", lazy=True)

    def set_password(self, password: str):
        """Hash and store password."""
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        self.password_hash = f"{salt}:{hashed}"

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        if not self.password_hash:
            return True  # no password set — allow login
        try:
            salt, hashed = self.password_hash.split(":")
            return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
        except Exception:
            return False

    def update_score(self, points: int):
        """Add points to total score."""
        self.total_score = (self.total_score or 0) + points
        db.session.commit()

    def to_dict(self):
        return {
            "id":             self.id,
            "username":       self.username,
            "total_score":    self.total_score or 0,
            "streak":         self.streak or 0,
            "topic_progress": self.topic_progress or "{}",
            "created_at":     self.created_at.isoformat() if self.created_at else None,
            "last_seen":      self.last_seen.isoformat() if self.last_seen else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"