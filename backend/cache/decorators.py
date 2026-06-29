import json
import inspect
import hashlib
import logging
from functools import wraps
from typing import Callable, Any
from fastapi import Request

from backend.cache.cache_service import cache_service

logger = logging.getLogger("cache_decorators")

def cache(namespace: str, ttl_seconds: int):
    """
    Decorator for caching FastAPI router endpoints.
    Automatically serializes path parameters, query parameters, and request payloads.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not cache_service.enabled:
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            # 1. Attempt to find Request object to get URL path and query parameters
            request: Request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request = val
                        break

            # 2. Build unique, deterministic cache key
            key_parts = []
            if request:
                key_parts.append(request.url.path)
                query_params = dict(request.query_params)
                if query_params:
                    key_parts.append(json.dumps(query_params, sort_keys=True))
            
            # Serialize arguments/kwargs (filtering out database session dependencies)
            clean_kwargs = {}
            for k, v in kwargs.items():
                if k in ("db", "session") or hasattr(v, "execute"):
                    continue
                if hasattr(v, "model_dump"):
                    clean_kwargs[k] = v.model_dump()
                elif hasattr(v, "dict"):
                    clean_kwargs[k] = v.dict()
                else:
                    clean_kwargs[k] = v
                    
            if clean_kwargs:
                kwargs_str = json.dumps(clean_kwargs, sort_keys=True, default=str)
                kwargs_hash = hashlib.sha256(kwargs_str.encode("utf-8")).hexdigest()
                key_parts.append(kwargs_hash)

            cache_key = f"{namespace}:{':'.join(key_parts)}" if key_parts else f"{namespace}:{func.__name__}"

            # 3. Read check
            cached = cache_service.get(cache_key)
            if cached is not None:
                return cached

            # 4. Miss - execute route
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 5. Write to Redis
            serializable = result
            if hasattr(result, "model_dump"):
                serializable = result.model_dump()
            elif hasattr(result, "dict"):
                serializable = result.dict()
            elif isinstance(result, list):
                serializable = []
                for item in result:
                    if hasattr(item, "model_dump"):
                        serializable.append(item.model_dump())
                    elif hasattr(item, "dict"):
                        serializable.append(item.dict())
                    else:
                        serializable.append(item)

            cache_service.set(cache_key, serializable, ttl_seconds)
            return result
        return wrapper
    return decorator
