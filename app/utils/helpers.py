import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


def format_price(price: float, currency: str = '$') -> str:
    """Format price with currency symbol"""
    return f"{currency}{price:,.2f}"


def sanitize_string(text: str) -> str:
    """Sanitize input string to prevent XSS"""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Escape special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text.strip()


def validate_price(price: Any) -> Optional[float]:
    """Validate and convert price to float"""
    try:
        price_float = float(price)
        if price_float < 0:
            return None
        return price_float
    except (ValueError, TypeError):
        return None


def validate_rating(rating: Any) -> Optional[float]:
    """Validate rating (0-5)"""
    try:
        rating_float = float(rating)
        if 0 <= rating_float <= 5:
            return rating_float
        return None
    except (ValueError, TypeError):
        return None


def generate_product_id(vendor: str, name: str) -> str:
    """Generate unique product ID"""
    import hashlib
    identifier = f"{vendor}_{name}".lower()
    return hashlib.md5(identifier.encode()).hexdigest()[:12]


def calculate_average_rating(ratings: List[float]) -> float:
    """Calculate average rating"""
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


class ResponseFormatter:
    """Format API responses consistently"""
    
    @staticmethod
    def success(data: Any, message: str = "Success", status_code: int = 200) -> Dict:
        """Format success response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'status_code': status_code,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400, details: Any = None) -> Dict:
        """Format error response"""
        response = {
            'success': False,
            'error': message,
            'status_code': status_code,
            'timestamp': datetime.utcnow().isoformat()
        }
        if details:
            response['details'] = details
        return response
    
    @staticmethod
    def paginated(data: List[Any], page: int, per_page: int, total: int) -> Dict:
        """Format paginated response"""
        return {
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'timestamp': datetime.utcnow().isoformat()
        }