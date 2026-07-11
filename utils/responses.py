"""
Response helpers
----------------
Consistent JSON response builders for all API routes.
"""

from flask import jsonify


def success(data: dict = None, message: str = "Success", status: int = 200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def error(message: str, status: int = 400, details=None):
    payload = {"success": False, "error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status
