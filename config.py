import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = "pyquest-secret-key-2026"

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'puzzle_game.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama-3.1-8b-instant"

    SANDBOX_TIMEOUT = 3

    ALLOWED_DIFFICULTIES = [
        "easy",
        "medium",
        "hard"
    ]

    ALLOWED_TOPIC_PREFIXES = [
        "variables and identifiers",
        "data types",
        "input and output",
        "operators",
        "conditional statements",
        "loops",
        "string manipulation",
        "lists",
        "tuples",
        "sets",
        "dictionaries",
        "functions",
        "exception handling",
        "file handling",
        "object-oriented programming"
    ]
}