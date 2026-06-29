import json
import logging
from typing import Any, Optional, Dict
from backend.cache.redis_client import get_redis_client
from backend.config.settings import settings

logger = logging.getLogger("cache_service")

# Default TTL durations in seconds
TTL_RECOMMENDATION = 15 * 60  # 15 min
TTL_DASHBOARD = 5 * 60        # 5 min
TTL_FORECAST = 30 * 60       # 30 min
TTL_HEALTH = 10 * 60         # 10 min
TTL_EMBEDDING = 24 * 60 * 60 # 24 hours
TTL_SEARCH = 30 * 60         # 30 min
TTL_EMPLOYEE = 24 * 60 * 60  # 24 hours
TTL_PROJECT = 24 * 60 * 60   # 24 hours
TTL_COPILOT_SESSION = 1 * 60 * 60 # 1 hour for session/history

class CacheService:
    def __init__(self):
        self.enabled = settings.CACHE_ENABLED

    def get(self, key: str) -> Optional[Any]:
        """Fetches value from cache, increments hits/misses metrics."""
        if not self.enabled:
            return None
            
        try:
            client = get_redis_client()
            val = client.get(key)
            if val is not None:
                client.incr("metrics:hits")
                try:
                    return json.loads(val)
                except ValueError:
                    return val
            else:
                client.incr("metrics:misses")
                return None
        except Exception as e:
            logger.error(f"Error reading cache key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Stores value in cache with a TTL limit."""
        if not self.enabled:
            return False
            
        try:
            client = get_redis_client()
            serialized = json.dumps(value, default=str)
            return bool(client.setex(key, ttl_seconds, serialized))
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Deletes key from cache."""
        if not self.enabled:
            return False
        try:
            client = get_redis_client()
            return bool(client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def invalidate_namespace(self, namespace: str) -> int:
        """Finds and deletes all keys belonging to a namespace pattern."""
        if not self.enabled:
            return 0
            
        try:
            client = get_redis_client()
            pattern = f"{namespace}:*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    client.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break
                    
            if deleted_count > 0:
                logger.info(f"Invalidated namespace '{namespace}': cleared {deleted_count} keys.")
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating namespace {namespace}: {e}")
            return 0

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates cache metrics, hit ratios, memory usage, and key counts."""
        if not self.enabled:
            return {"status": "disabled"}
            
        try:
            client = get_redis_client()
            info = client.info()
            
            # Fetch atomic hit/miss counters
            hits = int(client.get("metrics:hits") or 0)
            misses = int(client.get("metrics:misses") or 0)
            total = hits + misses
            hit_ratio = round((hits / total * 100.0), 2) if total > 0 else 0.0
            
            # Scan total key count
            key_count = client.dbsize()
            
            return {
                "status": "active",
                "hits": hits,
                "misses": misses,
                "hit_ratio_percentage": hit_ratio,
                "key_count": key_count,
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_bytes": info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.error(f"Error fetching cache metrics: {e}")
            return {"status": "error", "message": str(e)}

# Instantiate global service
cache_service = CacheService()
