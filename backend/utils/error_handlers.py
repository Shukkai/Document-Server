"""
Error handlers for Document Center
"""

from flask import jsonify
from werkzeug.exceptions import RequestEntityTooLarge


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        return jsonify({"error": "File too large"}), 413
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden"}), 403
    
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400 