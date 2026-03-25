import time
import json
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List
import threading
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Analytics service for tracking user behavior and performance"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.queries = defaultdict(int)
        self.search_times = []
        self.clicks = defaultdict(int)
        self.errors = defaultdict(int)
        self.performance_metrics = []
        
        # Create data directory if not exists
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Load existing data
        self.load_data()
        
        logger.info("Analytics service initialized")
    
    def track_search(self, query: str, result_count: int, duration: float):
        """Track search query"""
        self.queries[query.lower()] += 1
        self.search_times.append({
            'query': query,
            'count': result_count,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 1000 searches
        if len(self.search_times) > 1000:
            self.search_times = self.search_times[-1000:]
        
        logger.debug(f"Tracked search: {query} ({result_count} results, {duration:.2f}s)")
        self.save_data()
    
    def track_click(self, product_id: str, vendor: str, price: float):
        """Track product click"""
        self.clicks[f"{vendor}_{product_id}"] += 1
        logger.debug(f"Tracked click: {product_id} from {vendor}")
        self.save_data()
    
    def track_error(self, error_type: str, endpoint: str):
        """Track error occurrence"""
        self.errors[f"{error_type}_{endpoint}"] += 1
        logger.warning(f"Tracked error: {error_type} on {endpoint}")
        self.save_data()
    
    def track_performance(self, endpoint: str, duration: float, status: int):
        """Track API performance"""
        self.performance_metrics.append({
            'endpoint': endpoint,
            'duration': duration,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 1000 metrics
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Get most popular search queries"""
        sorted_queries = sorted(self.queries.items(), key=lambda x: x[1], reverse=True)
        return [{'query': q, 'count': c} for q, c in sorted_queries[:limit]]
    
    def get_avg_search_time(self) -> float:
        """Get average search time"""
        if not self.search_times:
            return 0.0
        return sum(s['duration'] for s in self.search_times) / len(self.search_times)
    
    def get_error_stats(self) -> Dict:
        """Get error statistics"""
        return {
            'total_errors': sum(self.errors.values()),
            'errors_by_type': dict(self.errors)
        }
    
    def get_api_performance(self) -> Dict:
        """Get API performance metrics"""
        if not self.performance_metrics:
            return {'avg_response_time': 0, 'total_requests': 0}
        
        avg_time = sum(m['duration'] for m in self.performance_metrics) / len(self.performance_metrics)
        return {
            'avg_response_time': avg_time,
            'total_requests': len(self.performance_metrics),
            'success_rate': sum(1 for m in self.performance_metrics if m['status'] < 400) / len(self.performance_metrics) * 100
        }
    
    def save_data(self):
        """Save analytics data to disk"""
        try:
            data = {
                'queries': dict(self.queries),
                'search_times': self.search_times[-100:],  # Save last 100
                'clicks': dict(self.clicks),
                'errors': dict(self.errors)
            }
            
            with open(os.path.join(self.data_dir, 'analytics.json'), 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save analytics: {e}")
    
    def load_data(self):
        """Load analytics data from disk"""
        try:
            file_path = os.path.join(self.data_dir, 'analytics.json')
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.queries = defaultdict(int, data.get('queries', {}))
                    self.search_times = data.get('search_times', [])
                    self.clicks = defaultdict(int, data.get('clicks', {}))
                    self.errors = defaultdict(int, data.get('errors', {}))
                logger.info("Analytics data loaded")
        except Exception as e:
            logger.error(f"Failed to load analytics: {e}")


# Global analytics instance
analytics = AnalyticsService()