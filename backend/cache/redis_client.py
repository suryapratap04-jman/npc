import redis
import logging
import time
import fnmatch
from typing import Optional, Any
from backend.config.settings import settings

logger = logging.getLogger("redis_client")

_connection_pool: Optional[redis.ConnectionPool] = None
_use_mock: bool = False

class MockRedis:
    """
    Fallback in-memory Redis mock client for resilience.
    Ensures caching works seamlessly even if the Docker Redis container is stopped.
    """
    def __init__(self):
        self._store = {}
        self._ttls = {}
        self._metrics = {"metrics:hits": "0", "metrics:misses": "0"}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> Optional[str]:
        if key in self._metrics:
            return self._metrics[key]
        if key in self._store:
            expire_at = self._ttls.get(key, float('inf'))
            if time.time() > expire_at:
                del self._store[key]
                del self._ttls[key]
                return None
            return self._store[key]
        return None

    def set(self, key: str, value: Any) -> bool:
        self._store[key] = str(value)
        self._ttls.pop(key, None)
        return True

    def setex(self, key: str, time_secs: int, value: Any) -> bool:
        self._store[key] = str(value)
        self._ttls[key] = time.time() + time_secs
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                self._ttls.pop(k, None)
                count += 1
            elif k in self._metrics:
                del self._metrics[k]
                count += 1
        return count

    def incr(self, key: str) -> int:
        if key not in self._metrics:
            self._metrics[key] = "0"
        val = int(self._metrics[key]) + 1
        self._metrics[key] = str(val)
        return val

    def exists(self, key: str) -> bool:
        if key in self._metrics:
            return True
        if key in self._store:
            expire_at = self._ttls.get(key, float('inf'))
            if time.time() > expire_at:
                del self._store[key]
                del self._ttls[key]
                return False
            return True
        return False

    def dbsize(self) -> int:
        return len(self._store)

    def flushdb(self) -> bool:
        self._store.clear()
        self._ttls.clear()
        self._metrics = {"metrics:hits": "0", "metrics:misses": "0"}
        return True

    def info(self) -> dict:
        return {
            "used_memory_human": "150KB (Mock Fallback)",
            "used_memory": 153600,
            "connected_clients": 1
        }

    def scan(self, cursor: int = 0, match: Optional[str] = None, count: int = 10):
        keys = list(self._store.keys()) + list(self._metrics.keys())
        if match:
            matched_keys = fnmatch.filter(keys, match)
        else:
            matched_keys = keys
        return 0, matched_keys

def get_redis_pool() -> redis.ConnectionPool:
    """Returns or initializes the global Redis connection pool."""
    global _connection_pool
    if _connection_pool is None:
        logger.info(f"Initializing Redis connection pool on {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        _connection_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_timeout=3,
            socket_keepalive=True,
            retry_on_timeout=True
        )
    return _connection_pool

_mock_redis_client: Optional[MockRedis] = None

def get_redis_client() -> Any:
    """Returns a real Redis client or falls back to in-memory MockRedis on connection failure."""
    global _use_mock, _mock_redis_client
    if _use_mock:
        if _mock_redis_client is None:
            _mock_redis_client = MockRedis()
        return _mock_redis_client
        
    try:
        pool = get_redis_pool()
        client = redis.Redis(connection_pool=pool)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Unable to connect to Redis server ({e}). Gracefully falling back to in-memory MockRedis caching.")
        _use_mock = True
        if _mock_redis_client is None:
            _mock_redis_client = MockRedis()
        return _mock_redis_client

def verify_redis_connection() -> bool:
    """Verifies Redis is reachable or returns True if MockRedis is active."""
    if not settings.CACHE_ENABLED:
        logger.info("Caching is disabled in configurations.")
        return False
    try:
        client = get_redis_client()
        return bool(client.ping())
    except Exception:
        return False
