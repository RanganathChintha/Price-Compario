from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException
import traceback
from app.utils.logger import logger


class APIError(Exception):
    """Custom API Exception"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert error to dictionary"""
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


def register_error_handlers(app):
    """Register error handlers for Flask app"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        logger.warning(f"404 error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Resource not found',
                'status_code': 404
            }), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"500 error: {error}\n{traceback.format_exc()}")
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'status_code': 500
            }), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        logger.error(f"API Error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Handle any unhandled exception"""
        logger.error(f"Unhandled exception: {error}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'status_code': 500
        }), 500