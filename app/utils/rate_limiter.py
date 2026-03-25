import time
from collections import defaultdict
from functools import wraps
from flask import request, jsonify
import threading


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request"""
        now = time.time()
        minute_ago = now - 60
        
        with self.lock:
            # Clean old requests
            self.requests[client_id] = [t for t in self.requests[client_id] if t > minute_ago]
            
            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self.requests[client_id].append(now)
            return True


def rate_limit(requests_per_minute=60):
    """Decorator for rate limiting routes"""
    limiter = RateLimiter(requests_per_minute)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = request.remote_addr
            if not limiter.is_allowed(client_id):
                return jsonify({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60
                }), 429
            return func(*args, **kwargs)
        return wrapper
    return decorator