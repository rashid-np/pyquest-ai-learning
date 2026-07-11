import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template
from config import Config
from database import init_db
from routes import auth_bp, questions_bp, submissions_bp, interview_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(interview_bp)

    # Serve the frontend
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "python-puzzle-game"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
