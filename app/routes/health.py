from flask import Blueprint, jsonify
import platform
import sys
import os
from datetime import datetime
from app.services.cache import product_cache
from app.services.analytics import analytics

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Detailed health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'system': {
            'python': sys.version,
            'platform': platform.platform(),
            'environment': os.environ.get('FLASK_ENV', 'production')
        },
        'cache': {
            'size': product_cache.get_stats()['size'],
            'max_size': product_cache.get_stats()['max_size']
        },
        'analytics': {
            'total_searches': len(analytics.search_times),
            'total_clicks': sum(analytics.clicks.values())
        },
        'uptime': get_uptime()
    })


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed health check with performance metrics"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'performance': analytics.get_api_performance(),
        'errors': analytics.get_error_stats(),
        'popular_searches': analytics.get_popular_searches(5),
        'cache_stats': product_cache.get_stats(),
        'memory_usage': get_memory_usage()
    })


def get_uptime():
    """Calculate application uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return uptime_seconds
    except:
        return None


def get_memory_usage():
    """Get current memory usage"""
    import psutil
    try:
        process = psutil.Process(os.getpid())
        return {
            'rss': process.memory_info().rss / 1024 / 1024,  # MB
            'vms': process.memory_info().vms / 1024 / 1024   # MB
        }
    except:
        return None