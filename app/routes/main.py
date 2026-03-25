from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Price Compario API is running'
    })