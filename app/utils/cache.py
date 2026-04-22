"""
Simple in-memory cache with TTL support.
Used to cache categories, keywords, and other frequently accessed data.
"""
import time
from functools import wraps
from threading import Lock


class SimpleCache:
    """Thread-safe in-memory cache with TTL"""

    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def get(self, key):
        """Get value from cache if not expired"""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
        return None

    def set(self, key, value, ttl=300):
        """Set value in cache with TTL (default 5 minutes)"""
        with self._lock:
            expiry = time.time() + ttl if ttl else None
            self._cache[key] = (value, expiry)

    def delete(self, key):
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()

    def clear_prefix(self, prefix):
        """Clear all keys starting with prefix"""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]


# Global cache instance
cache = SimpleCache()


def cached(ttl=300, key_prefix=""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
