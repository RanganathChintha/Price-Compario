from cachetools import TTLCache
import logging
from typing import Any, Optional
import hashlib
import json

logger = logging.getLogger(__name__)


class ProductCache:
    """Cache service for product data with TTL support"""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time to live in seconds
            max_size: Maximum number of items in cache
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.ttl_seconds = ttl_seconds
        logger.info(f"Cache initialized with TTL {ttl_seconds}s, max size {max_size}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        try:
            value = self.cache.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set item in cache"""
        try:
            self.cache[key] = value
            logger.debug(f"Cache set for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get_or_set(self, key: str, func, *args, **kwargs) -> Any:
        """Get from cache or execute function and cache result"""
        cached = self.get(key)
        if cached is not None:
            return cached
        
        result = func(*args, **kwargs)
        if result:
            self.set(key, result)
        return result
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache
    
    def delete(self, key: str) -> bool:
        """Delete specific key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache deleted for key: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.cache.maxsize,
            'ttl_seconds': self.ttl_seconds
        }


# Global cache instance
product_cache = ProductCache()