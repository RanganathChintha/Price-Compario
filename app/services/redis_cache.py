import json
import logging
from typing import Any, Optional
import hashlib

logger = logging.getLogger(__name__)

# Try to import redis, but don't fail if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Using memory cache.")


class RedisCache:
    """Redis cache service with fallback to memory"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using memory cache.")
                self.redis_client = None
        
        # Fallback to memory cache
        self.memory_cache = {}
        self.use_redis = self.redis_client is not None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.use_redis:
            try:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return self.memory_cache.get(key)
        else:
            return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache"""
        try:
            if self.use_redis:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                self.memory_cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete from cache"""
        try:
            if self.use_redis:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.use_redis:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False


# Global cache instance
redis_cache = RedisCache()