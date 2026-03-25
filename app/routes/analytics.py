from flask import Blueprint, jsonify, request
from app.services.analytics import analytics
from app.utils.helpers import ResponseFormatter
from app.utils.logger import logger

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/analytics/popular', methods=['GET'])
def popular_searches():
    """Get popular search queries"""
    try:
        limit = request.args.get('limit', 10, type=int)
        popular = analytics.get_popular_searches(limit)
        return jsonify(ResponseFormatter.success(popular)), 200
    except Exception as e:
        logger.error(f"Error getting popular searches: {e}")
        return jsonify(ResponseFormatter.error('Failed to get analytics', 500)), 500


@analytics_bp.route('/api/analytics/stats', methods=['GET'])
def analytics_stats():
    """Get analytics statistics"""
    try:
        stats = {
            'avg_search_time': analytics.get_avg_search_time(),
            'error_stats': analytics.get_error_stats(),
            'performance': analytics.get_api_performance(),
            'total_searches': len(analytics.search_times),
            'total_clicks': sum(analytics.clicks.values())
        }
        return jsonify(ResponseFormatter.success(stats)), 200
    except Exception as e:
        logger.error(f"Error getting analytics stats: {e}")
        return jsonify(ResponseFormatter.error('Failed to get stats', 500)), 500


@analytics_bp.route('/api/analytics/track-click', methods=['POST'])
def track_click():
    """Track product click"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        vendor = data.get('vendor')
        price = data.get('price')
        
        if product_id and vendor:
            analytics.track_click(product_id, vendor, price)
            return jsonify(ResponseFormatter.success({'tracked': True})), 200
        
        return jsonify(ResponseFormatter.error('Missing required fields', 400)), 400
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        return jsonify(ResponseFormatter.error('Failed to track click', 500)), 500