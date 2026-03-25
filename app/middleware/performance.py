import time
from flask import request, g
from functools import wraps
from app.services.analytics import analytics
from app.utils.logger import logger


class PerformanceMiddleware:
    """Middleware to track performance metrics"""
    
    def __init__(self, app):
        self.app = app
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup middleware hooks"""
        
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                
                # Log slow requests
                if duration > 1.0:
                    logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
                
                # Track performance
                analytics.track_performance(
                    endpoint=request.path,
                    duration=duration,
                    status=response.status_code
                )
                
                # Add performance headers
                response.headers['X-Response-Time'] = f"{duration:.2f}s"
                response.headers['X-Request-ID'] = request.headers.get('X-Request-ID', 'N/A')
            
            return response


def cache_control(max_age=300, public=True):
    """Decorator to add cache control headers"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            cache_type = 'public' if public else 'private'
            response.headers['Cache-Control'] = f'{cache_type}, max-age={max_age}'
            return response
        return wrapper
    return decorator